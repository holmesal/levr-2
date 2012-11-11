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
			if query != 'all' and accepted_deals.__len__() != 0:
				t1 = datetime.now()
				packaged_deals = search.sort_and_package(accepted_deals)
				package_time = datetime.now()-t1
			else:
				# act like a search all, use all deals
				
				# decompose deals by origin
				levr_deals, foursquare_deals = search.filter_deals_by_origin(deals)
				
				if levr_deals.__len__() >5:
					t1 = datetime.now()
					packaged_deals = search.sort_and_package(levr_deals)
					package_time = datetime.now()-t1
				# qualify search results. do we need more?
				else:
					t1 = datetime.now()
					packaged_deals = search.sort_and_package(deals)
					package_time = datetime.now()-t1
					
					# add foursquare deals
					if foursquare_deals.__len__() < 5:
						# search for more foursquare deals
						try:
							# grab search information
							token = search.foursquare_token
							deal_status = search.deal_status
							foursquare_ids = search.get_foursquare_ids(deals)
							
							# make remote call to foursquare
							ft1 = datetime.now()
							new_foursquare_deals = api_utils.search_foursquare(geo_point,token,deal_status,foursquare_ids)
							
							times.update({'foursquare_search_time':str(datetime.now()-ft1)})
							
							# add new foursquare deals
							packaged_deals.extend(new_foursquare_deals)
						except:
							levr.log_error('Error in foursquare call or parsing.')
			times.update({'package_time':package_time})
#			else:
#				params = {
#							'lat'			:	geo_point.lat,
#							'lon'			:	geo_point.lon,
#							'token'			:	token,
#							'foursquare_ids':	foursquare_ids,
#							'deal_status'	:	deal_status
#						}
#				
#				logging.debug('Sending this to the task: ' + json.dumps(params))
#						
#				#start the task
#				taskqueue.add(url='/tasks/searchFoursquareTask',payload=json.dumps(params))
			
			
			
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
#					'ending_hashes'		: list(searched_hash_set),
					'num_total_results'		: packaged_deals.__len__(),
					'deals'				: packaged_deals,
					'times'				: times
					}
			try:
				response.update({
								'user' : api_utils.package_user(self.user, True, False)
								})
			except:
				levr.log_error()
			
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
class SearchPopularHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False,levrToken=False)
	def get(self,**kwargs):
		'''
		inputs: lat,lon,limit
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				searches :[string,string]
				}
		'''
		try:
			logging.info('SEARCH POPULAR\n\n\n')
			#GET PARAMS
			logging.debug(kwargs)
			request_point 	= kwargs.get('geoPoint')
#			radius 		= kwargs.get('radius')
#			limit 		= kwargs.get('limit')
			development = kwargs.get('development',False)
			
			logging.debug("request_point type: "+str(type(request_point)))
			logging.debug('')
			deals = []
			t1 = datetime.now()
			#fetch deals
			#hash the reuqested geo_point
			center_hash = geohash.encode(request_point.lat,request_point.lon,precision=5)
			logging.debug(center_hash)
			
			#get the hashes of the center geo_point and the 8 surrounding hashes
			hash_set = geohash.expand(center_hash)
			logging.debug(hash_set)
			
			#set deal status to active or test
			if development: deal_status = 'test'
			else: deal_status = 'active'
			
			for query_hash in hash_set:
				#only grab keys for deals that have active status
				q = levr.Deal.all(projection=['tags']).filter('deal_status',deal_status)
				#FILTER BY GEOHASH
				q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
				
#				logging.debug(levr.log_dir(q))
				#FETCH DEAL KEYS
				fetched_deals = q.fetch(None)
				logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
				
				deals.extend(fetched_deals)
		#					logging.debug(deal_keys)
			t2 = datetime.now()
			
			
			#===================================================================
			# Get all deal tags
			#===================================================================
			tags = []
			for deal in deals:
#				logging.debug(dir(deals))
				tags.extend(deal.tags)
			logging.debug(tags)
			
			# filter tags
			try:
				tags = filter(lambda x: x not in blacklist, tags)
			except:
				levr.log_error()
			#convert list of all tags to a dict of key=tag, val=frequency
			count = {}
			for tag in tags:
#					logging.debug(tag in count)
				if tag in count:
					count[tag] += 1
				else:
					count[tag] = 1
			
			#===================================================================
			# convert dict of tag:freq into list of tuples
			#===================================================================
			tuple_list = []
			for key in count:
				tuple_list.append((count[key],key))
				
			#sort tags by frequency, highest first
			tuple_list.sort()
			tuple_list.reverse()

			#select only the most popular ones, and convert to list
			word_list = [x[1] for x in tuple_list if x[1] not in blacklist]
			
			
			####DEBUG
			#if the popular items list is longer than 6, send entire list, else only send 6
			try:
				logging.debug(word_list.__len__())
				if word_list.__len__()<6:
					popular_items = word_list
				else:
					popular_items = word_list[:6]
			
			### SWITCH
			except:
				popular_items = word_list
				levr.log_error('popular searches')
			#### /DEBUG
			
			#BATCH GET RESULTS
			t3 = datetime.now()
			
			
			
			#create response dict
			response = {
					'numResults': popular_items.__len__(),
					'fetching'	: str(t2-t1),
					'packaging'	: str(t3-t2),
					'total'		: str(t3-t1),
					'searches'	: popular_items
					}
			api_utils.send_response(self,response)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

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