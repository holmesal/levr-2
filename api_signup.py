from google.appengine.ext import db
from random import randint
import api_utils
import api_utils_social as social
import json
import levr_classes as levr
import levr_encrypt as enc
import logging
import webapp2


class SignupFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteToken=True)
	def post(self,*args,**kwargs):
		#RESTRICTED
		try:
			#check token
			facebook_token	= kwargs.get('remoteToken',None)
			
#			user = levr.Customer.all().filter('facebook_id',facebook_id).get()
			
			user = social.Facebook(None,'verbose',facebook_token=facebook_token)
			try:
				new_user, new_user_details, new_friends = user.first_time_connect(
											facebook_token	= facebook_token,
											)
			except Exception,e:
				levr.log_error()
				assert False, 'Could not connect with facebook.'
			
			#return the user
			response = {
					'user':api_utils.package_user(new_user,True,send_token=True),
					'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
					'new_user_details'	: new_user_details
					}
			
			api_utils.send_response(self,response,new_user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
			

class SignupFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteToken=True)
	def post(self,*args,**kwargs):
		try:
			#check token
			foursquare_token = kwargs.get('remoteToken',None)
			
			user = levr.Customer.all().filter('foursquare_token',foursquare_token).get()
			
			if user:
				#fallback to login
				response = {
						'user':api_utils.package_user(user,True,send_token=True)
						}
			else:
				#===============================================================
				# NOTE: there is a remote chance that the users foursquare oauth_token would change.
				# this would not recognize that
				#===============================================================
				#create new user
				user = social.Foursquare()
				try:
					user, new_user_details, new_friends = user.first_time_connect(
													foursquare_token = foursquare_token
													)
				except Exception,e:
					#remove the entity that was created because the signup failed
					new_user.delete()
					levr.log_error()
					assert False, 'Could not connect with foursquare. '.format('')
				#return the user
				response = {
						'user':api_utils.package_user(user,True,send_token=True),
						'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
						'new_user_details'	: new_user_details
						}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class SignupTwitterHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=True,remoteToken=True,remoteTokenSecret=True)
	def post(self,*args,**kwargs):
		try:
			twitter_id				= int(kwargs.get('remoteID',None))
			twitter_token			= kwargs.get('remoteToken',None)
			twitter_token_secret	= kwargs.get('remoteTokenSecret',None)
			
			
			logging.debug('\n\n{}\n{}\n{}\n\n'.format(
											twitter_id,
											twitter_token,
											twitter_token_secret
											)
						)
			user = levr.Customer.all().filter('twitter_id',twitter_id).get()
			logging.debug(user)
			if user:
				#fallback to login
				logging.debug('User exists!')
				response = {
						'user':api_utils.package_user(user,True,send_token=True)
						}
			else:
				#create new user
				user = social.Twitter()
				try:
					user, new_user_details, new_friends = user.first_time_connect(
													twitter_id			= twitter_id,
													oauth_token			= twitter_token,
													oauth_token_secret	= twitter_token_secret
													)
				except Exception,e:
					#delete the new user that was created because the signup failed
					new_user.delete()
					levr.log_error()
					assert False, 'Could not connect with foursquare. '.format('')
				#return the user
				response = {
						'user':api_utils.package_user(user,True,send_token=True),
						'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
						'new_user_details'	: new_user_details
						}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class SignupLevrHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,email=True,alias=True,pw=True)
	def post(self,*args,**kwargs):
		#RESTRICTED
		try:
			logging.debug(kwargs)
			email = kwargs.get('email',None)
			alias = kwargs.get('alias',None)
			pw = kwargs.get('pw',None)
			
			'''Check availability of username+pass, create and login if not taken'''
			#check availabilities
			r_email = levr.Customer.gql('WHERE email = :1',email).get()
			r_alias  = levr.Customer.gql('WHERE alias = :1',alias).get()
			
			#if taken, send error
			if r_email:
				api_utils.send_error(self,'That email is already registered.')
				return
			if r_alias:
				api_utils.send_error(self,'That alias is already registered.')
				return
			
			#still here? create a customer, then.
			user 		= levr.Customer(levr_token=levr.create_levr_token())
			user.email = email
			user.pw 	= enc.encrypt_password(pw)
			user.alias = alias
			
			#create or refresh the alias
			user = levr.build_display_name(user)
			
			#put and reply
			user.put()
			response = {'user':api_utils.package_user(user,True,send_token=True)}
			api_utils.send_response(self,response,user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
app = webapp2.WSGIApplication([('/api/signup/facebook', SignupFacebookHandler),
								('/api/signup/foursquare', SignupFoursquareHandler),
								('/api/signup/twitter', SignupTwitterHandler),
								('/api/signup/levr.*', SignupLevrHandler)],debug=True)