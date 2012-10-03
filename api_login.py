import webapp2
import logging
import levr_classes as levr
import levr_encrypt as enc
import api_utils
from google.appengine.ext import db


class LoginFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,facebookID=True,token=True)
	def get(self,*args,**kwargs):
		#RESTRICTED
		try:
			#check token
			token = self.request.get('token')
			if token == '':
				api_utils.send_error(self,'Required parameter not passed: token')
				return
				
			#check if token currently exists in datastore
			existing_user = levr.Customer.all().filter('')
	#		gql('WHERE facebook_token = :1',token).get()
			
			if existing_user:
				#return the user
				response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
				api_utils.send_response(self,response,existing_user)
			else:
				api_utils.send_error(self,'Authentication failed.')
				return
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class LoginFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,token=True)
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('LOGIN FOURSQUARE\n\n\n')
			logging.debug(kwargs)
			#check token
			token = kwargs.get('token')
			
			#check if token currently exists in datastore
			existing_user = levr.Customer.gql('WHERE foursquare_token = :1',token).get()
			
			if existing_user:
				#return the user
				response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
				api_utils.send_response(self,response,existing_user)
			else:
				api_utils.send_error(self,'Authentication failed.')
				return
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class LoginTwitterHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,token=True)
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('LOGIN TWITTER\n\n\n')
			logging.debug(kwargs)
			#check token
			token = kwargs.get('token')
			#check token
			
			
			#check if token currently exists in datastore
			existing_user = levr.Customer.gql('WHERE twitter_token = :1',token).get()
			
			if existing_user:
				#return the user
				response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
				api_utils.send_response(self,response,existing_user)
			else:
				api_utils.send_error(self,'Authentication failed.')
				return
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class LoginLevrHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,email_or_owner=True,pw=True)
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('LOGIN LEVR\n\n\n')
			logging.debug(kwargs)
			
			email_or_owner = kwargs.get('email_or_owner')
			pw = kwargs.get('pw')
			
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
			
			#package user, private setting, send token
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			
			api_utils.send_response(self,response,existing_user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
app = webapp2.WSGIApplication([('/api/login/facebook', LoginFacebookHandler),
								('/api/login/foursquare', LoginFoursquareHandler),
								('/api/login/twitter', LoginTwitterHandler),
								('/api/login/levr', LoginLevrHandler)
								],debug=True)