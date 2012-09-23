import webapp2
import logging


class LoginFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass

class LoginFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass
		
class LoginTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass
		
class LoginLevrHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass	
		
app = webapp2.WSGIApplication([('/api/login/facebook', LoginFacebookHandler),
								('/api/login/foursquare', LoginFoursquareHandler),
								('/api/login/twitter', LoginTwitterHandler),
								('/api/login/levr', LoginLevrHandler)],debug=True)