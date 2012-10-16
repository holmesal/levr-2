from datetime import datetime,timedelta
from google.appengine.ext import db
import api_utils
import api_utils_social as social
import levr_classes as levr
import levr_encrypt as enc
import logging
import random
import webapp2


class LoginFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=True,remoteToken=False)
	def get(self,*args,**kwargs):
		#=======================================================================
		# This is not finished. Do not use.
		#=======================================================================
		#RESTRICTED
		try:
			token 		= kwargs.get('remoteToken')
			facebook_id = int(kwargs.get('remoteID'))
			
			user = levr.Customer.all().filter('facebook_id',facebook_id).get()
			assert user, 'Facebook user is not registered with Levr, remoteID: {}'.format(facebook_id)
			
			#TODO: update users facebook info
			
			response = {
					'user':api_utils.package_user(user,True,send_token=True)
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class LoginFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=False,remoteToken=True)
	def get(self,*args,**kwargs):
		try:
			#===================================================================
			# This is not finished. Do not use.
			#===================================================================
			
			#RESTRICTED
			logging.debug('LOGIN FOURSQUARE\n\n\n')
			logging.debug(kwargs)
			
			#check token
			foursquare_id	= kwargs.get('remoteID',None)
			foursquare_token= kwargs.get('remoteToken',None)
			
			#find user with matching credentials
			if foursquare_id:
				user = levr.Customer.all().filter('foursquare_id',foursquare_id).get()
			else:
				#
				user = levr.Customer.all().filter('foursquare_token',foursquare_token).get()
			
			#if user could not be found, their foursquare_token might have changed
			#consult foursquare
			if not user:
				### HACKY WORKAROUND
				#spoof user object
				user = levr.Customer()
				user = social.Foursquare(user)
				#add foursquare credentials
				user.foursquare_id = foursquare_id
				user.foursquare_token = foursquare_token
				
				try:
					#connect to foursquare, and grab new info
					new_user_details = user.update_user_details()
				except Exception,e:
					#could not connect to foursquare
					assert False, 'Foursquare user is not registered with Levr: {}'.format(e)
				### /HACKY WORKAROUND
			
			response = {
					'user':api_utils.package_user(existing_user,True,send_token=True)
					}
			api_utils.send_response(self,response,existing_user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class LoginTwitterHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=True,remoteToken=True,remoteTokenSecret=True)
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('LOGIN TWITTER\n\n\n')
			logging.debug(kwargs)
			#check token
			twitter_id				= int(kwargs.get('remoteID'))
			twitter_token			= kwargs.get('remoteToken')
			twitter_token_secret	= kwargs.get('remoteTokenSecret')
			#check token
			
			#find the user with the specified twitter_id
			user = levr.Customer.all().filter('twitter_id',twitter_id).get()
			
			#assure that a user exists with this twitter id
			assert user, 'Twitter user is not registered with Levr, remoteID: {}'.format(twitter_id)
			logging.debug(user.twitter_token_secret != twitter_token_secret)
			logging.debug(user.twitter_token != twitter_token)
			#authenticate user from the server and update info
			if user.twitter_token != twitter_token or user.twitter_token_secret != twitter_token_secret:
				#the users auth token does not match, but may have changed. check with twitter.
				logging.debug('{} != {}'.format(user.twitter_token,twitter_token))
				logging.debug('{} != {}'.format(user.twitter_token_secret,twitter_token_secret))
				user = social.Twitter(user)
				
				try:
					logging.debug('eee')
					new_user, new_user_details, new_friends = user.first_time_connect(
																				
																				twitter_id = twitter_id,
																				twitter_token = twitter_token,
																				twitter_token_secret = twitter_token_secret
																				)
					logging.debug('eee')
				except Exception,e:
					#failed authentication
					#TODO: when error handling on the remote responses is improved, this will change
					assert False, 'User could not be authenticated with Twitter. '.format(e)
				else:
					response = {
							'user'				: api_utils.package_user(new_user,True,send_token=True),
							}
			else:
				logging.debug('{} == {}'.format(user.twitter_token,twitter_token))
				logging.debug('{} == {}'.format(user.twitter_token_secret,twitter_token_secret))
				logging.debug('THEY ARE EQUAL')
				#credentials are matched. 
				#TODO: run task to update users information
				#return the user
				response = {
						'user':api_utils.package_user(user,True,send_token=True)
						}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error {}'.format(e))
			
			
class LoginLevrHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,email_or_owner=True,pw=True)
	def get(self,*args,**kwargs):
		'''
		A user logs in with levr using an email or alias, and a password
		'''
		try:
			#RESTRICTED
			logging.debug('LOGIN LEVR\n\n\n')
			logging.debug(kwargs)
			
			email_or_owner = kwargs.get('email_or_owner')
			pw = kwargs.get('pw')
			pw = enc.encrypt_password(pw)
			
			
			#check both email and password
			
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
			
			#create or refresh the alias
			existing_user = levr.build_display_name(existing_user)
			
			#===================================================================
			# Spoof Ninja Activity!
			#===================================================================
			
			data = api_utils.SpoofUndeadNinjaActivity(existing_user).run()
			logging.debug(levr.log_dict(data))
			#set last login
			existing_user = data['user']
			#still here? update last login by putting
			existing_user.put()
			
			#package user, private setting, send token
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			
			api_utils.send_response(self,response,existing_user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class LoginValidateHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			#grabthe user from the input
			user = kwargs.get('actor')
			
			response = {'user':api_utils.package_user(user,True)}
			
			try:
				data = api_utils.SpoofUndeadNinjaActivity(user).run()
				logging.debug(levr.log_dict(data))
				#set last login
				user = data['user']
			except:
				levr.log_error()
				
			user.date_last_login = datetime.now()
#			logging.debug(user.date_last_login)
			user.put()
			api_utils.send_response(self,response,user)
			
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class Test(webapp2.RequestHandler):
	def get(self):
		user = levr.Customer.all().filter('email','ethan@levr.com').get()
		
		output = api_utils.SpoofUndeadNinjaActivity(user).run()
		api_utils.send_response(self,output)
		
		
		
		
	
	
	
	
app = webapp2.WSGIApplication([('/api/login/facebook', LoginFacebookHandler),
								('/api/login/foursquare', LoginFoursquareHandler),
								('/api/login/twitter', LoginTwitterHandler),
								('/api/login/levr', LoginLevrHandler),
								('/api/login/validate', LoginValidateHandler),
								('/api/login/test', Test)
								],debug=True)