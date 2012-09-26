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
			logging.debug('SEARCH\n\n\n\n')
#			logging.debug(levr.log_dir(self.request))
			
			DEFAULT_RANGE = 2 #miles
			DEFAULT_LIMIT = None
			
			lat		= self.request.get('lat')
			lon		= self.request.get('lon')
			range	= self.request.get('range')#optional
			limit	= self.request.get('limit') #optional
			
			
			
			if not lat:
				raise KeyError('lat: '+lat)
			if not lon:
				raise KeyError('lon: '+lon)
			if not range:
				range = DEFAULT_RANGE
			if not limit:
				limit = DEFAULT_LIMIT
			
			
			if not lat.isdigit():
				raise TypeError('lat: '+lat)
			if not lon.isdigit():
				raise TypeError('lon: '+lon)
			if limit and not limit.isdigit():
				raise TypeError('limit: '+limit)
			
			#convert lat, lon to a single geo_point
			geo_string = str(lat)+","+str(lon)
			geo_point = levr.geo_converter(geo_string)
			
			
			paths = self.request.path.split('/')
			path = paths[paths.__len__()-1]
			logging.debug(path)
		
		except KeyError,e:
			api_utils.send_error(self,'Required paramter not passed, '+str(e))
		except TypeError,e:
			api_utils.send_error(self,'Invalid parameter, '+str(e))
		else:
			handler_method(self,query,geo_point,range,limit)
	
	return check_params



class SearchQueryHandler(webapp2.RequestHandler):
	@validate
	def get(self,query,geo_point,range,limit):
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
			logging.debug(query)
			logging.debug(geo_point)
			logging.debug(limit)
			logging.debug(self.request.params)
			
			#create search tags
			tags = levr.tagger(query.lower())
			
			
			#fetch all deals from within range
			deals = api_utils.get_deals_in_area(tags,geo_point,range,limit)
			
			
		except:
			levr.log_error(self.request.params)


class SearchNewHandler(webapp2.RequestHandler):
	@validate
	def get(self,query,geo_point,range,limit):
		'''
		inputs: lat,lon,limit,range
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
	def get(self,query,geo_point,range,limit):
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
	def get(self,query,geo_point,range,limit):
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