import webapp2
import logging
import levr_classes as levr
import levr_encrypt as enc
import api_utils
from google.appengine.ext import db


class LoginFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
			
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE facebook_token = :1',token).get()
		
		if existing_user:
			#return the user
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			api_utils.send_response(self,response,existing_user)
		else:
			api_utils.send_error(self,'Authentication failed.')
			return

class LoginFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
			
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE foursquare_token = :1',token).get()
		
		if existing_user:
			#return the user
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			api_utils.send_response(self,response,existing_user)
		else:
			api_utils.send_error(self,'Authentication failed.')
			return
		
class LoginTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
			
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE twitter_token = :1',token).get()
		
		if existing_user:
			#return the user
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			api_utils.send_response(self,response,existing_user)
		else:
			api_utils.send_error(self,'Authentication failed.')
			return
		
class LoginLevrHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check email_or_owner
		email_or_owner = self.request.get('email_or_owner')
		if email_or_owner == '':
			api_utils.send_error(self,'Required parameter not passed: email_or_owner')
			return
		#check password
		pw = self.request.get('pw')
		if pw == '':
			api_utils.send_error(self,'Required parameter not passed: pw')
			return
			
		#check both email and password
		pw = enc.encrypt_password(pw)
		r_email = levr.Customer.gql('WHERE email = :1 AND pw=:2',email_or_owner,pw).get()
		r_alias  = levr.Customer.gql('WHERE alias = :1 AND pw=:2',email_or_owner,pw).get()
		if r_email:
			#match based on email
			existing_user = r_email
		elif r_alias:
			#match based on alias
			existing_user = r_alias
		else:
			api_utils.send_error(self,'Authentication failed.')
			return
		
		#still here? update last login by putting
		existing_user.put()
		response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
		api_utils.send_response(self,response,existing_user)
		
app = webapp2.WSGIApplication([('/api/login/facebook', LoginFacebookHandler),
								('/api/login/foursquare', LoginFoursquareHandler),
								('/api/login/twitter', LoginTwitterHandler),
								('/api/login/levr', LoginLevrHandler)],debug=True)