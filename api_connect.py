import webapp2
import logging


class ConnectFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass

class ConnectFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass
		
class ConnectTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass
		
class ConnectLevrHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass	
		
app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler),
								('/api/connect/levr', ConnectLevrHandler)],debug=True)