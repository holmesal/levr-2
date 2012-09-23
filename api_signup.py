import webapp2
import logging
import api_utils
import levr_classes as levr
from google.appengine.ext import db


class SignupFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.missing_param(self,'token')
			return
		
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE facebook_token = :1',token).get()
		
		if existing_user:
			#user already exists and is trying to log in again, return this user
			pass
		else:
			#user does not exist, create new and populate via facebook API
			pass

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