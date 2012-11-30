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



class SearchQueryHandler(api_utils.BaseClass):
	@api_utils.validate('query',None,
					geoPoint=False,
					ll=False,
					radius=False,
					user=False,
					latitudeHalfDelta=False,
					longitudeHalfDelta=False)
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		inputs: lat,lon,limit, query
		response:{
			[string,string]
			}
		/api/search/all?
		lat=42.357632
		&lon=-71.089432
		&limit=50
		&offset=0
		&uid=tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51St9sfoYChA=
		&levrToken=7ALUawsTs1R3_z_pK0YTx4cCkpfSFzuDCOM1XQCXWDM
		&latitudeHalfDelta=0.023277
		&longitudeHalfDelta=0.027466
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
class SearchPopularHandler(api_utils.BaseClass):
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
			# if there arent enough levr deals, include the foursquare ones
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
						if deal.origin == 'foursquare':
							rank += 1.
						else:
							rank += 2.
						
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

class SearchFoursquareHandler(webapp2.RequestHandler):
	'''
	Search only returns ALL of the existing foursquare deals every time
	'''
	def get(self):
		try:
			#should only return deals with a foursquare_id set
			deals = levr.Deal.all().filter('foursquare_id >','').fetch(None)
			logging.debug('number of foursquare deals: '+str(deals.__len__()))
			
#			for deal in deals:
#				assert deal.foursquare_id, 'A deal was returned that does not have a foursquare id. change the query.'
			return_deals = [api_utils.package_deal(deal) for deal in deals if deal.foursquare_id]
			
			
			response = {
					'foursquareDeals' : return_deals,
					'numFoursquareDeals' : return_deals.__len__()
					}
			api_utils.send_response(self,response)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
app = webapp2.WSGIApplication([(r'/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search/foursquare', SearchFoursquareHandler),
								('/api/search/(.*)', SearchQueryHandler)
								
								],debug=True)