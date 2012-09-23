import webapp2
import logging


class SearchNewHandler(webapp2.RequestHandler):
	def get(self):
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
			levr.log_error(levr_utils.log_dir(self.request))
class SearchHotHandler(webapp2.RequestHandler):
	def get(self):
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
	def get(self):
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
class SearchQueryHandler(webapp2.RequestHandler):
	def get(self):
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
			pass
		except:
			levr.log_error(self.request.params)
		
app = webapp2.WSGIApplication([('/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search.*', SearchQueryHandler)],debug=True)