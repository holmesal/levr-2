from common_word_list import blacklist
from datetime import datetime
from google.appengine.api import taskqueue
from google.appengine.ext import db
import api_utils
import geo.geohash as geohash
import json
import levr_classes as levr
import logging
import random
import webapp2
from tasks import INCREMENT_DEAL_VIEW_URL

class FindABusinessHandler(api_utils.BaseClass):
	'''
	A handler for searching for a specific venue
	'''
	@api_utils.validate(None, 'param',
					user = False,
					levrToken = False,
					# fields to identify a business
					businessName = False,
					vicinity = False,
					geoPoint = True,
					radius = False,
					)
	def get(self,*args,**kwargs):
		'''
		@return: <business>
		'''
		logging.info(kwargs)
		business_name = kwargs.get('businessName')
		vicinity = kwargs.get('vicinity')
		geo_point = kwargs.get('geoPoint')
		radius = kwargs.get('radius') # TODO: implement radius to search
		try:
			# create a set of geo hashes to search based on the radius
			search = api_utils.Search(True)
			precision = 5
			ghash_list,bounding_box = search.create_ghash_list(geo_point, precision)
			
			logging.info(ghash_list)
			# get deal keys
			for ghash in ghash_list:
				business_keys = levr.Business.all(keys_only=True
											).filter('geo_hash_prefixes',ghash
											).fetch(None)
			
			# fetch all businesses
			businesses = db.get(business_keys)
			
			# filter the businesses by the tags
			search_tags = set([])
			if business_name:
				search_tags.update(levr.create_tokens(business_name))
			if vicinity:
				search_tags.update(levr.create_tokens(vicinity))
			logging.info(search_tags)
			# map the quality of the match by the number of tags that match the business
			for business in businesses:
				business_tags = business.tags
				business.rank = 0
				for tag in business_tags:
					if tag in search_tags:
						business.rank += 1
			# assure that a business was found
			assert businesses, 'Could not find a business'
			# sort the businesses by their quality
			ranks = [b.rank for b in businesses]
			toop = zip(ranks,businesses)
			toop.sort()
			ranks,businesses = zip(*toop)
			
			# get the highest ranking business
			business = businesses[0]
			
			# get all deals from that business
			deals = levr.Deal.all(keys_only=True
								).ancestor(business.key()
								).filter('deal_status',levr.DEAL_STATUS_ACTIVE
								).fetch(None)
			
			packaged_deals = api_utils.package_deal_multi(deals)
			packaged_business = api_utils.package_business(business)
			response = {
					'business' : packaged_business,
					'deals' : packaged_deals
					}
			self.send_response(response)
		except AssertionError,e:
			self.send_error(e)
		except Exception,e:
			levr.log_error()
			self.send_error()
class ViewABusinessHandler(api_utils.BaseClass):
	'''
	A handler to view the deals at a specific venue
	'''
	@api_utils.validate(None, 'param',
					user = False,
					levrToken = False,
					business = True
					)
	def get(self,*args,**kwargs):
		user = kwargs.get('actor')
		business = kwargs.get('business')
		development = kwargs.get('development',False)
		
		try:
			deals = api_utils.fetch_all_businesses_deals(business, development)
			
			# TODO: take another look at the business packaging for the api
			# package.
			packaged_deals = api_utils.package_deal_multi(deals, False)
			
			packaged_business = api_utils.package_business(business)
			
			# respond
			response = {
					'deals' : packaged_deals,
					'business' : packaged_business
					}
			self.send_response(response)
		except:
			levr.log_error()
			self.send_error()

FIND_A_BUSINESS_URL = '/api/business/find'
VIEW_A_BUSINESS_URL = '/api/business/view'
app = webapp2.WSGIApplication([
							(FIND_A_BUSINESS_URL, FindABusinessHandler),
							(VIEW_A_BUSINESS_URL, ViewABusinessHandler),
								],debug=True)