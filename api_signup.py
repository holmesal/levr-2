import webapp2
import logging


class SignupFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass

class SignupFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass
		
class SignupTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass
		
class SignupLevrHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		pass	
		
app = webapp2.WSGIApplication([('/api/signup/facebook', SignupFacebookHandler),
								('/api/signup/foursquare', SignupFoursquareHandler),
								('/api/signup/twitter', SignupTwitterHandler),
								('/api/signup/levr', SignupLevrHandler)],debug=True)