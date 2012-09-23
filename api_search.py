import webapp2
import logging


class SearchNewHandler(webapp2.RequestHandler):
	def get(self):
		pass
		
class SearchHotHandler(webapp2.RequestHandler):
	def get(self):
		pass
		
class SearchPopularHandler(webapp2.RequestHandler):
	def get(self):
		pass
		
class SearchQueryHandler(webapp2.RequestHandler):
	def get(self):
		pass
		
app = webapp2.WSGIApplication([('/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search.*', SearchQueryHandler)],debug=True)