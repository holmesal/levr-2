import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
import geo.geohash as geohash

from datetime import datetime
from google.appengine.ext import db



def validate(handler_method):
	'''
	Validation decorator for all of the search methods
	'''
	def check_params(self,query=None):
		try:
			logging.debug('SEARCH DECORATOR\n\n\n\n')
#			logging.debug(levr.log_dir(self.request))
			logging.warning(query)
			
			DEFAULT_RADIUS = 2 #miles
			DEFAULT_LIMIT = None
			
			lat		= self.request.get('lat')
			lon		= self.request.get('lon')
			radius	= self.request.get('radius')#optional
			limit	= self.request.get('limit') #optional
			
			
			#GRAB PARAMETERS
			if not lat		: raise KeyError('lat: '+lat)
			if not lon		: raise KeyError('lon: '+lon)
			if not radius	: radius = DEFAULT_RADIUS
			if not limit	: limit = DEFAULT_LIMIT
			
			#CHECK PARAMETERS
			try: float(lat)
			except: raise TypeError('lat: '+lat)
			
			try: float(lon)
			except: raise TypeError('lon: '+lon)
			
			if limit and not limit.isdigit():
				raise TypeError('limit: '+limit)
			
			#convert lat, lon to a single geo_point
			geo_string = str(lat)+","+str(lon)
			geo_point = levr.geo_converter(geo_string)
			
			
			logging.debug(radius)
			logging.debug(limit)
			
		except KeyError,e:
			api_utils.send_error(self,'Required paramter not passed, '+str(e))
		except TypeError,e:
			api_utils.send_error(self,'Invalid parameter, '+str(e))
		else:
			handler_method(self,query=query,geo_point=geo_point,radius=radius,limit=limit)
	
	return check_params

#def validate(*a,**to_validate):
#	'''
#	General function for validating the inputs that are passed as arguments
#	to use, pass kwargs in form of key:bool,
#	where key is the input name and bool is true if required and false if optional
#	'''
#	
#	def wrapper(handler_method):
#		'''
#		This is the decorator that operates on the function being decorated
#		I dont understand this. Gah!
#		'''
#		def validator(self,*args,**kwargs):
#			logging.debug('Validator')
#			logging.debug(args)
#			logging.debug(kwargs)
#			logging.debug(kwargs)
#			logging.debug(a)
#			logging.debug(to_validate)
#			
#			c = levr.Customer.all().get()
#			logging.debug(type(c))
#			logging.debug(type(c.key()))
#			try:
#				type_cast = {
#						'limit'	: int,
#						'lat'	: float,
#						'lon'	: float,
#						'radius': float,
#						'since'	: int,
#						'uid'	: levr.Customer,
#						'dealID': levr.Deal,
#						}
#				defaults = {
#						'limit'	: 30,
#						'lat'	: 42.349798,
#						'lon'	: -71.120000,
#						'radius': 2,
#						'since'	: None,
#						}
#				
#				for (key,required) in to_validate.iteritems():
#					logging.debug(type(key))
#					logging.debug(key)
#					val			= self.request.get(key)
#					required	= to_validate.get(key)
#					data_type	= type_cast[key]
#					msg			= key+": "+val
#					
#					logging.debug(val)
#					logging.debug(data_type)
#					logging.debug(msg)
#					logging.debug(required)
#					if not val:
#						if required:
#							raise KeyError(msg)
#						else:
#							#not required, set to default value
#							val = defaults[key]
#					elif data_type == int and not val.isdigit():
#						#integer input is not valid
#						raise TypeError(msg)
#					elif data_type == float:
#						#float input is not valid
#						try:
#							val = float(val)
#						except ValueError,e:
#							raise KeyError(msg)
#					elif data_type == db.Key:
#						#key input is not valid
#						val = enc.decrypt_key(val)
#						if key == 'uid' and type(val) != levr.Customer:
#							raise KeyError(msg)
#						elif key == 'dealID' and type(val) != levr.Deal:
#							raise KeyError(msg)
#					kwargs.update({key:val})
#						
#				lat = kwargs.get('lat')
#				lon = kwargs.get('lon')
#				if lat and lon:
#					#check geopoint
#					try:
#						geo_point = levr.geo_converter(str(lat)+','+str(lon))
#						kwargs.update({'geo_point':geo_point})
#					except:
#						levr.log_error()
#						raise TypeError('lat,lon: '+str(lat)+","+str(lon))
#				logging.debug(kwargs)
#				
#			except KeyError,e:
#				api_utils.send_error(self,'Required paramter not passed, '+str(e))
#			except TypeError,e:
#				api_utils.send_error(self,'Invalid parameter, '+str(e))
#			except Exception,e:
#				levr.log_error()
#				api_utils.send_error(self,'Server Error: '+str(e))
#			else:
#				return handler_method(self,*args,**kwargs)
#		
#		return validator
#	
#	return wrapper

class SearchQueryHandler(webapp2.RequestHandler):
	@validate #(lat=True,lon=True,limit=False,uid=True)
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
			geo_point 	= kwargs.get('geo_point')
			radius 		= kwargs.get('radius')
			limit 		= kwargs.get('limit')
			query 		= kwargs.get('query','all')
			
			logging.debug("limit: "+str(limit))
			
			#create tags from the query
			tags = levr.tagger(query)
			logging.debug("tags: "+str(tags))
			
			t1 = datetime.now()
			#fetch deals
			deals = api_utils.get_deals_in_area(tags,geo_point,radius,limit)
			
			t2 = datetime.now()
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
	@validate
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
	@validate
	def get(self,**kwargs):
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
			logging.debug(query)
			logging.info("\n\nSEARCH NEW")
			
		except:
			levr.log_error(levr_utils.log_dir(self.request))
			api_utils.send_error('Server Error')

class SearchHotHandler(webapp2.RequestHandler):
	@validate
	def get(self,query,geo_point,radius,limit):
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
	@validate
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
			request_point 	= kwargs.get('geo_point')
			radius 		= kwargs.get('radius')
			limit 		= kwargs.get('limit')
			
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
				
				logging.debug(levr.log_dir(q))
				#FETCH DEAL KEYS
				fetched_deals = q.fetch(None)
				logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
				
				deals.extend(fetched_deals)
		#					logging.debug(deal_keys)
			t2 = datetime.now()
			
			#FILTER
			tags = []
			for deal in deals:
				logging.debug(dir(deals))
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