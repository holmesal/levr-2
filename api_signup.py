import webapp2
import logging
import api_utils
import levr_classes
from google.appengine.ext import db


class SignupFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			self.response.out.write(api_utils.missing_param('token'))
			return
			
		#check if token currently exists in datastore
		
		

class SignupFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			self.response.out.write(api_utils.missing_param('token'))
			return
		
class SignupTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			self.response.out.write(api_utils.missing_param('token'))
			return
		
class SignupLevrHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			self.response.out.write(api_utils.missing_param('token'))
			return	
		
app = webapp2.WSGIApplication([('/api/signup/facebook', SignupFacebookHandler),
								('/api/signup/foursquare', SignupFoursquareHandler),
								('/api/signup/twitter', SignupTwitterHandler),
								('/api/signup/levr', SignupLevrHandler)],debug=True)