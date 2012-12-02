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
from common_word_list import popular_blacklist
from google.appengine.ext import testbed
import unittest


class SearchQueryHandler(api_utils.BaseHandler):
#	@api_utils.validate('query', None,
#					ghashes=False,
#					ll=False,
#					user=False,
#					levrToken=False,
#					limit=False,
#					offset=False
#					)
	def get(self,*args,**kwargs):
		'''
		Searches for deals in the ghashes provided
		OR takes a geo_point and searches in that area
		'''
#		ghash_list = kwargs.get('ghashes',[])
#		geo_point = kwargs.get('geo_point',None)
#		query = kwargs.get('query','all')
#		development = kwargs.get('development',False)
#		limit = kwargs.get('limit',50)
#		offset = kwargs.get('offset',0)
#		user = kwargs.get('actor',None)
		
		try:
			### SPOOF ###
			development = False
			user = None
			### /SPOOF
			# init the search class
			search = api_utils.Search(development,user)
			
			
			### SPOOF ###
			precision = 5
			geo_point = levr.geo_converter('42.343880,-71.059570')
			query = 'food'
			ghash_list = search.create_ghash_list(geo_point, precision)
			
			### /SPOOF ###
			
			
			deals = search.fetch_deals(ghash_list, include_foursquare=True)
			search_tags = search.tokenize_query(query)
			query_ranks = search.rank_deals_by_tag(deals, search_tags)
			related_ranks = search.rank_deals_by_kw_links(deals, search_tags)
			popularity_ranks = search.rank_deals_by_popularity(deals)
			toop = zip(query_ranks,related_ranks,popularity_ranks,deals)
			toop = sorted(toop)
			
			query_ranks,related_ranks,popularity_ranks,deals = zip(*toop)
			
			self.response.headers['Content-Type'] = 'text/plain'
			for dt in toop:
				self.response.out.write('\n{}, {}, {}, {}'.format(dt[0],dt[1],dt[2],dt[3].tags))
		except:
			self.send_fail()
		
		
class SearchSuggestedHandler(api_utils.BaseHandler):
#	@api_utils.validate(None, 'param',
#					user=True,
#					levrToken=True,
#					ghashes=True
#					)
	def get(self,*args,**kwargs):
		'''
		A user is searching for deals that we suggest for them
		'''
#		user = kwargs.get('actor')
#		development = kwargs.get('development')
		try:
			#===================================================================
			# SPOOF
			user = db.get(db.Key.from_path('Customer','pat'))
			development = False
			#===================================================================
			
			# init search class
			search = api_utils.SuggestedSearch(development,user)
			
			#===================================================================
			# SPOOF
			geo_point = levr.geo_converter('42.343880,-71.059570')
			ghash_list = search.create_ghash_list(geo_point, precision=5)
			#===================================================================
			
			# grab all the relevant deals
			clicked_deals = search.fetch_clicked_deals()
			upvoted_deals,clicked_deals = search.filter_upvoted_deals(clicked_deals)
			
			# extract all the tags from all of the deals
			clicked_deal_tags = search.flatten_deal_tags(clicked_deals)
			upvoted_deal_tags = search.flatten_deal_tags(upvoted_deals)
			
			# create a dict of tag:rank
			ranked_tags = search.calc_tag_ranks(clicked_deal_tags, search._clicked_deal_tag_strength, rank_dict=None)
			ranked_tags = search.calc_tag_ranks(upvoted_deal_tags, search._upvoted_deal_tag_strength, rank_dict=ranked_tags)
			
			# search for deals in the area, do not fetch duplicates
			existing_deals = upvoted_deals + clicked_deals
			existing_deal_keys = [deal.key() for deal in existing_deals]
			new_deals = search.fetch_deals(ghash_list, existing_deal_keys)
			
			# combine deal lists
			deals = new_deals + existing_deals
			
			# rank deals
			suggested_ranks = search.rank_deals_by_ranked_tags(deals, ranked_tags)
			popularity_ranks = search.rank_deals_by_popularity(deals)
			
			# sort deals by ranks
			
		except:
			self.send_fail()
		
class SearchNewHandler(api_utils.BaseHandler):
	@api_utils.validate(None,None,
					geoPoint=True,
					limit=False,
					radius=False,
					user=False)
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		inputs: lat,lon,limit,radius
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				[string,string]
				}
		'''
		try:
			logging.info("\n\nSEARCH NEW")
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

class SearchHotHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		inputs: lat,lon,limit
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				[string,string]
				}
		'''
		try:
			pass
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class SearchPopularHandler(api_utils.BaseHandler):
	@api_utils.validate(None,None,
					geoPoint=True,
					)
	def get(self,**kwargs):
		'''
		inputs: lat,lon,limit
		response:{
			searches :[string,string]
			}
		'''
		try:
			logging.info('\n\n\n SEARCH POPULAR\n\n\n')
			geo_point 	= kwargs.get('geoPoint')
#			radius 		= kwargs.get('radius')
#			limit 		= kwargs.get('limit')
			development = kwargs.get('development',False)
			
			search = api_utils.Search(development)
			
			# create ghash list
			precision = 5
			ghash_list = search.create_ghash_list(geo_point, precision)
			
			# fetch all of the deals!
			deals = search.fetch_deals(ghash_list)
			
			if not deals:
				# don't move. I'm watching you!
				response = {
					'numResults': 0,
					'searches'	: []
					}
				self.send_response(response)
				return
			# filter out all the repeat deals i.e. the same fs deal at multiple locations
			unique_deal_texts = []
			unique_deals = []
			for deal in deals:
				deal_text = deal.deal_text
				if deal_text not in unique_deal_texts:
					unique_deal_texts.append(deal_text)
					unique_deals.append(deal)
			
			deals = unique_deals
			# grab all of the tags from the deals
			for deal in deals:
				deal.raw_tags = deal.create_tags(stemmed=False,include_business=False)
			
#			assert False, sorted([d.tags for d in deals])
			
			
			
			# get a big ol' list of all the tags
			tags = set([tag for deal in deals for tag in deal.raw_tags])
			tags = sorted(tags)
			
			# filter out popular search blacklisted terms
			tags = filter(lambda x: x not in popular_blacklist,tags)
			
			logging.info('\n'.join(tags))
			
			# init ranks toop for scoring the deals
			toops = []
			
			# rank the deals according to criteria
			for tag in tags:
				rank = 0
				for deal in deals:
					if tag in deal.raw_tags:
						rank += 1.
						
						rank += deal.upvotes/10.
						
				toops.append((rank,tag))
			# sort deals based on their ranks
			toops = sorted(toops,reverse=True)
			for toop in toops:
				logging.info(toop)
#			assert False, toops
			ranks,tags = zip(*toops) #@UnusedVariable
			
			
			#if the popular items list is longer than 6, send entire list, else only send 6
			try:
				logging.debug(tags.__len__())
				if tags.__len__()<6:
					popular_items = tags
				else:
					popular_items = tags[:6]
			
			except:
				popular_items = tags
				levr.log_error('popular searches')
			
			
			#create response dict
			response = {
					'numResults': popular_items.__len__(),
					'searches'	: popular_items
					}
			self.send_response(response)
		except:
			levr.log_error()
			self.send_error()

app = webapp2.WSGIApplication([(r'/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search/(.*)', SearchQueryHandler)
								
								],debug=True)
