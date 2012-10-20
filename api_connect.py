from google.appengine.ext import db
import api_utils
import api_utils
import api_utils_social as social
import levr_classes as levr
import levr_encrypt as enc
import logging
import webapp2

class ConnectFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,remoteToken=True,levrToken=True)
	@api_utils.private
	def post(self,*args,**kwargs):
		try:
			#RESTRICTED
			user			= kwargs.get('actor',None)
			facebook_token	= kwargs.get('remoteToken',None)
			
			user = social.Facebook(user,'verbose')
			
			try:
				user, new_user_details, new_friends = user.first_time_connect(
											facebook_token	= facebook_token,
											)
			except Exception,e:
				levr.log_error()
				assert False, 'Could not connect with facebook.'
			
			
			#return the user
			response = {
					'user':api_utils.package_user(user,True),
					'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
					'new_user_details'	: new_user_details
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

class ConnectFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,remoteToken=True,levrToken=True)#id=True
	@api_utils.private
	def post(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('CONNECT FOURSQUARE\n\n\n')
			logging.debug(kwargs)
			
			user					= kwargs.get('actor')
			foursquare_token		= kwargs.get('remoteToken')
			
			#===================================================================
			# Check to see if there are multiple accounts
			# i.e. the user that is connecting w/ foursquare has an existing fs account with levr
			#===================================================================
			# check for an existing foursquare user
			foursquare_user = levr.Customer.all().filter('foursquare_token',foursquare_token).get()
			# If a user was found in the db with the requested foursquare credentials, 
			# and that user is not the same user as the one requesting the connection, 
			# merge the foursquare created account into the requesting user (i.e. the levr account user)
			if foursquare_user and foursquare_user is not user:
				#this means the user has multiple accounts that need to be merged
				user,donor = api_utils.merge_customer_info_from_B_into_A(user,foursquare_user,'foursquare')
			# Otherwise, act normally. Simply connect. If the user already has foursquare credentials, 
			# this will refresh their foursquare information
			else:
				#create an instance of the Foursquare social connection class
				user = social.Foursquare(user,'verbose')
				
				try:
					user, new_user_details, new_friends = user.first_time_connect(
													foursquare_token = foursquare_token
													)
				except Exception,e:
					levr.log_error()
					assert False, 'Could not connect with foursquare. '.format('')
			
			response = {
					'user'				: api_utils.package_user(user,True),
					'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
					'new_user_details'	: new_user_details
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class ConnectTwitterHandler(webapp2.RequestHandler):
#	@api_utils.validate(None,None,user=False,token=False,screenName=False,levrToken=False)
	@api_utils.validate(None,'param',user=True,remoteToken=True,remoteTokenSecret=True,remoteID=True,levrToken=True)
	@api_utils.private
	def post(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('CONNECT TWITTER\n\n\n')
			logging.debug(kwargs)
			
			user		= kwargs.get('actor')
			twitter_token	= kwargs.get('remoteToken')
			twitter_token_secret = kwargs.get('remoteTokenSecret')
			twitter_id	= kwargs.get('remoteID')
			development = kwargs.get('development')
			
			user = social.Twitter(user,'verbose')
			
			try:
				user, new_user_details, new_friends = user.first_time_connect(
												twitter_id			= twitter_id,
												twitter_token			= twitter_token,
												twitter_token_secret	= twitter_token_secret
												)
			except Exception,e:
				#delete the new user that was created because the signup failed
				levr.log_error()
				assert False, 'Could not connect with foursquare. '.format('')
			
			#return the user
			response = {
					'user':api_utils.package_user(user,True),
					'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
					'new_user_details'	: new_user_details
					}
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class TestConnectionHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.debug("\n\n\nTEST HANDLER\n\n\n")
			u = self.request.get('user')
			if u == 'ethan':
				user = levr.Customer.all().filter('email','ethan@levr.com').get()
			elif u == 'pat':
				user = levr.Customer.all().filter('email','patrick@levr.com').get()
			elif u == 'alonso':
				user = levr.Customer.all().filter('email','alonso@levr.com').get()
			elif u == 'run':
				ethan = levr.Customer.all().filter('email','ethan@levr.com').get()
				alonso = levr.Customer.all().filter('email','alonso@levr.com').get()
				pat = levr.Customer.all().filter('email','alonso@levr.com').get()
			
			
			
			
				#pat connects with foursquare
				p = social.Facebook(pat)
				a = social.Foursquare(alonso)
				e = social.Twitter(ethan)
				
				logging.debug('\n\n\n\t\t\t PAT CONNECTS  \n\n\n')
				#pat connects with foursquare
				patch = p.first_time_connect(
									foursquare_token = pat.facebook_token
									)
				
				logging.debug('\n\n\n\t\t\t ALONSO CONNECTS \n\n\n')
				al = a.first_time_connect(
									foursquare_token = alonso.foursquare_token
									)
				
				logging.debug('\n\n\n\t\t\t ETHAN CONNECTS \n\n\n')
				#ethan connects with twitter
				twitter_token = 'default'
				twitter_token_secret = 'default'
				twitter_token = ethan.twitter_token
				twitter_token_secret = ethan.twitter_token_secret
				eth = e.first_time_connect(
									twitter_screen_name = ethan.twitter_screen_name
									)
				
				response = {
						'pat' : {
								'user':api_utils.package_user(patch[0],True),
								'new_details': patch[1],
								'new_friends': [str(f) for f in patch[2]]
								},
						'alonso' : {
								'user':api_utils.package_user(al[0],True),
								'new_details': al[1],
								'new_friends': [str(f) for f in al[2]]
								},
						'ethan'	: {
								'user':api_utils.package_user(eth[0],True),
								'new_details': eth[1],
								'new_friends': [str(f) for f in eth[2]]
								},
						}
				
			method = self.request.get('method')
			if method == 'foursquare':
				fs_id = user.foursquare_id
				fs_token = user.foursquare_token
				u = social.Foursquare(user,'verbose')
				user, new_user_details, new_friends = u.first_time_connect(foursquare_token=fs_token)
				response = {
						'user':api_utils.package_user(user,True),
						'new_details': new_user_details,
						'new_friends': [str(f) for f in new_friends]
						}
			
			elif method == 'twitter':
				user = levr.Customer.all().filter('email','ethan@levr.com').get()
				u = social.Twitter(user,'verbose','debug')
				twitter_screen_name = user.twitter_screen_name
#				twitter_id			= user.twitter_id
				user, new_user_details, new_friends = u.first_time_connect(
									twitter_screen_name	=twitter_screen_name,
#									twitter_id			=twitter_id
									)
				response = {
						'user':api_utils.package_user(user,True),
						'new_details': new_user_details,
						'new_friends': [str(f) for f in new_friends]
						}
			elif method == 'facebook':
				u = social.Facebook(user,'verbose','debug')
				facebook_id	= 1234380397
				facebook_token = 'AAACEdEose0cBAF9BQo5IWPc6JlgGAMZAZCy50ZBIpJ3psytKfzBaiqm2d0fYi8UrVMOVpew9S9ZCkM3gEAVbDQZAKb15AJI5ZChzLkjIMZBTG4fhQkBvGu6'
				user, new_user_details,new_friends = u.first_time_connect(True
																		)
				response = {
						'user':api_utils.package_user(user,True),
						'new_details': new_user_details,
						'new_friends': [str(f) for f in new_friends]
						}
			api_utils.send_response(self,response,None)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler),
								('/api/connect/test', TestConnectionHandler)
								],debug=True)