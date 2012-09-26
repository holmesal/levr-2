import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
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
			
			
			paths = self.request.path.split('/')
			path = paths[paths.__len__()-1]
			logging.debug(path)
			
			logging.debug(radius)
			logging.debug(limit)
			
		except KeyError,e:
			api_utils.send_error(self,'Required paramter not passed, '+str(e))
		except TypeError,e:
			api_utils.send_error(self,'Invalid parameter, '+str(e))
		else:
			handler_method(self,query,geo_point,radius,limit)
	
	return check_params



class SearchQueryHandler(webapp2.RequestHandler):
	@validate
	def get(self,query,geo_point,rad,limit):
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


class SearchNewHandler(webapp2.RequestHandler):
	@validate
	def get(self,query,geo_point,radius,limit):
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
			logging.info("\n\nSEARCH")
			
		except:
			levr.log_error(levr_utils.log_dir(self.request))
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
class SearchPopularHandler(webapp2.RequestHandler):
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

		
app = webapp2.WSGIApplication([('/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search/(.*)', SearchQueryHandler)
								],debug=True)