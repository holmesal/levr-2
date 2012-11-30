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


class SearchQueryHandler_v2(api_utils.BaseHandler):
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
			related_ranks = search.rank_deals_by_links(deals, search_tags)
			popularity_ranks = search.rank_deals_by_popularity(deals)
			toop = zip(query_ranks,related_ranks,popularity_ranks,deals)
			toop = sorted(toop)
			
			query_ranks,related_ranks,popularity_ranks,deals = zip(*toop)
			
			self.response.headers['Content-Type'] = 'text/plain'
			for dt in toop:
				self.response.out.write('\n{}, {}, {}, {}'.format(dt[0],dt[1],dt[2],dt[3].tags))
		except:
			self.send_fail()
		
		
		
class SearchQueryHandler(api_utils.BaseHandler):
	@api_utils.validate('query',None,
					geoPoint=False,
					ll=False,
					radius=False,
					user=False,
					latitudeHalfDelta=False,
					longitudeHalfDelta=False)
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		'''
		try:
			tstart = datetime.now()
			
			logging.debug('SEARCH BY QUERY \n\n\n')
	#		logging.debug(kwargs)
			#GET PARAMS
			logging.info(kwargs)
			#assert False
			geo_point 		= kwargs.get('geoPoint')
#			radius 			= kwargs.get('radius')
#			limit 			= kwargs.get('limit')
			query 			= kwargs.get('query','all')
			development		= kwargs.get('development',False)
			user 			= kwargs.get('actor')
			lon_half_delta	= kwargs.get('longitudeHalfDelta',0)
#			lat_half_delta	= kwargs.get('latitudeHalfDelta')
			
			try:
				logging.info(user.display_name)
			except:
				logging.info('unkown user')
			
			
			times = {}
			search = api_utils.Search(development,user)
			# calc precision
			precision = search.calc_precision_from_half_deltas(geo_point, lon_half_delta)
			# create ghashes
			ghash_list = search.create_ghash_list(geo_point, precision)
			# calc bounding box
			bounding_box = search.calc_bounding_box(ghash_list)
			
			# fetch all deals in the ghash range
			t1 = datetime.now()
			deals = search.fetch_deals(ghash_list)
			times.update({'fetch_deals_time':str(datetime.now() - t1)})
			
			# filter deals by search query
			t1 = datetime.now()
			num_results,accepted_deals= search.filter_deals_by_query(deals, query)
			times.update({'filter_deals_time': str(datetime.now() - t1)})
			
			
			# increment deal views on levr deals
			search.add_deal_views(deals)
			
			# init package time
			t1 = datetime.now()
			if query != 'all' and accepted_deals.__len__() != 0:
				packaged_deals = search.sort_and_package(accepted_deals)
			else:
				# act like a search all, use all deals
				packaged_deals = search.sort_and_package(deals)
			times.update({'package_time':datetime.now() - t1})
			
			
			times.update({'total_time':datetime.now()-tstart})
			
			
			#===================================================================
			# Send response
			#===================================================================
			logging.info(levr.log_dict(times))
			
			times = {key:str(times[key]) for key in times}
			response = {
					'searchPoint'		: str(geo_point),
					'numResults'		: num_results,
					'boundingBox'		: bounding_box,
					'num_total_results'		: packaged_deals.__len__(),
					'deals'				: packaged_deals,
					'times'				: times
					}
			try:
				response.update({
								'user' : api_utils.package_user(self.user, True, False)
								})
			except:
				logging.info('user not passed')
			
#			assert False, response
			self.send_response(response)
		except:
			levr.log_error()
			self.send_error()

class SearchNewHandler(webapp2.RequestHandler):
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
