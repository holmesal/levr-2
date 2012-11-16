#from google.appengine.ext import db
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
			
			logging.debug(levr.log_model_props(user))
			logging.debug(str(new_user_details))
			
			#return the user
			response = {
					'user':api_utils.package_user(user,True),
					'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
					'new_user_details'	: new_user_details
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e.message))
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
			
			user				= kwargs.get('actor')
			foursquare_token	= kwargs.get('remoteToken')
			new_user_details	= None
			new_friends			= None
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
				data = api_utils.merge_customer_info_from_B_into_A(user,foursquare_user,'foursquare')
				user = data[0]
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
					'user'				: api_utils.package_user(user,True)
#					'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
#					'new_user_details'	: new_user_details
					}
			if new_user_details: response['new_user_details'] = new_user_details
			if new_friends: response['new_friends'] = new_friends
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e.message))
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
#			development = kwargs.get('development')
			
			user = social.Twitter(user,'verbose')
			
			try:
				user, new_user_details, new_friends = user.first_time_connect(
												twitter_id			= twitter_id,
												twitter_token			= twitter_token,
												twitter_token_secret	= twitter_token_secret
												)
			except Exception,e:
				levr.log_error(e)
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

app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler)
								],debug=True)