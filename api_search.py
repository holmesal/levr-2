import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
import geo.geohash as geohash

from datetime import datetime
from google.appengine.ext import db



class SearchQueryHandler(webapp2.RequestHandler):
	@api_utils.validate('query',None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,*args,**kwargs):
		'''
		inputs: lat,lon,limit, query
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
			logging.debug('SEARCH BY QUERY\n\n\n')
	#		logging.debug(kwargs)
			#GET PARAMS
			logging.debug(kwargs)
			geo_point 	= kwargs.get('geoPoint')
			radius 		= kwargs.get('radius')
			limit 		= kwargs.get('limit')
			query 		= kwargs.get('query','all')
			
			development = kwargs.get('development',False)
			
			
			
			logging.debug("limit: "+str(limit))
			
			#create tags from the query
			tags = levr.tagger(query)
			logging.debug("tags: "+str(tags))
			
			t1 = datetime.now()
			#fetch deals
			deals = api_utils.get_deal_keys(tags,geo_point,radius,limit,development=development)
			
			t2 = datetime.now()
			
			#FILTER THE DEALS BY DISTANCE
			filtered_deals = api_utils.filter_deals_by_radius(deals,request_point,radius)
	
			
			#package deals
			packaged_deals = [api_utils.package_deal(deal) for deal in deals]
			
			t3 = datetime.now()
			
			geo_hash = geohash.encode(geo_point.lat,geo_point.lon)
			
			logging.debug(geo_hash)
			deals = levr.Deal.all().fetch(None)
			for deal in deals:
				logging.debug(levr.log_model_props(deal,['geo_hash']))
			
	#		packaged_deals.append(api_utils.package_deal(deal))
			#create response dict
			response = {
					'numResults': packaged_deals.__len__(),
					'fetching'	: str(t2-t1),
					'packaging'	: str(t3-t2),
					'total'		: str(t3-t1),
					'deals'		: packaged_deals
					}
			api_utils.send_response(self,response)
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')
class LoadTestHandler(webapp2.RequestHandler):
	@api_utils.validate('query',None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,**kwargs):
		'''
		inputs: lat,lon,limit, query
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
			logging.info("\n\nSEARCH")
#			logging.debug(query)
#			logging.debug(geo_point)
#			logging.debug(limit)
#			logging.debug(self.request.params)
#			
			#create search tags
			tags = levr.tagger(query.lower())
			p = [6,5,4]
			r = [1,2,3,4,5,6,7,8,9,10]
			
			response = {
					'results': []
					}
			start = datetime.now()
			
			for radius in r:
				for precision in p:
			
					t1 = datetime.now()
					#fetch all deals from within radius
					(deals,fetch_time,get_time,filter_time,unfiltered_count,filtered_count) = api_utils.get_deals_in_area(tags,geo_point,radius,limit,precision)
					
					t2 = datetime.now()
					
					packaged_deals = [api_utils.package_deal(deal) for deal in deals]
					
					t3 = datetime.now()
					response['results'].append({
											'precision' : str(precision),
											'radius'	: str(radius),
											'unfiltered_count': str(unfiltered_count),
											'filtered_count'  : str(filtered_count),
											'getting'	: {
															'fetching'	: str(fetch_time),
															'getting'	: str(get_time),
															'filtering' : str(filter_time),
															'total'		: str(t2-t1)
															},
											'packaging'	: str(t3-t2),
											'total'		: str(t3-t1)
											})
#					response = {
#							'numResults': packaged_deals.__len__(),
#							'fetching'	: str(t2-t1),
#							'packaging'	: str(t3-t2),
#							'total'		: str(t3-t1)
#		#					'deals'		: packaged_deals
#							}
			
			end = datetime.now()
			response['time'] = str(end-start)
			
			api_utils.send_response(self,response)
			
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')

class SearchNewHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,*args,**kwargs):
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
			levr.log_error(levr.log_dir(self.request))
			api_utils.send_error(self,'Server Error')

class SearchHotHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,*args,**kwargs):
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
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')
class SearchPopularHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
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
			request_point 	= kwargs.get('geoPoint')
			radius 		= kwargs.get('radius')
			limit 		= kwargs.get('limit')
			
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
			
			for query_hash in hash_set:
				#only grab keys for deals that have active status
				q = levr.Deal.all(projection=['tags']).filter('deal_status =','active')
				#FILTER BY GEOHASH
				q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
				
#				logging.debug(levr.log_dir(q))
				#FETCH DEAL KEYS
				fetched_deals = q.fetch(None)
				logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
				
				deals.extend(fetched_deals)
		#					logging.debug(deal_keys)
			t2 = datetime.now()
			
			#FILTER
			tags = []
			for deal in deals:
#				logging.debug(dir(deals))
				tags.extend(deal.tags)
			logging.debug(tags)
			
			#convert list of all tags to a dict of key=tag, val=frequency
			count = {}
			for tag in tags:
#					logging.debug(tag in count)
				if tag in count:
					count[tag] += 1
				else:
					count[tag] = 1
			
			#convert dict of tag:freq into list of tuples
			tuple_list = []
			for key in count:
				tuple_list.append((count[key],key))
				
			#sort tags by frequency, highest first
			tuple_list.sort()
			tuple_list.reverse()
			
			#select only the most popular ones, and convert to list
			word_list = [x[1] for x in tuple_list]
			
			#if the popular items list is longer than 6, send entire list, else only send 6
			logging.debug(word_list.__len__())
			if word_list.__len__()<6:
				popular_items = word_list
			else:
				popular_items = word_list[:6]
			
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
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')

		
app = webapp2.WSGIApplication([(r'/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search/(.*)', SearchQueryHandler)
								],debug=True)