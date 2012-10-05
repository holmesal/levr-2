import webapp2
import logging
import api_utils
import levr_classes as levr
import levr_encrypt as enc
import api_utils_social as social
import api_utils
from google.appengine.ext import db

class ConnectFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,token=True,facebookID=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		#RESTRICTED
		user		= kwargs.get('actor')
		token		= kwargs.get('token')
		facebook_id	= kwargs.get('facebookID')
		
		
		
		#add facebook token
		user.facebook_token = token
		#fetch user info from facebook graph api
		user = social.facebook_deets(user,facebook_id,token)
		
		#create or refresh the alias
		user = levr.build_display_name(user)
		
		#update
		user.put()
		
		#return the user
		response = {
				'user':api_utils.package_user(user,True)
				}
		api_utils.send_response(self,response,user)


class ConnectFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,token=True,levrToken=True)
	@api_utils.private
	def post(self,*args,**kwargs):
		#RESTRICTED
		logging.debug('CONNECT FOURSQUARE\n\n\n')
		logging.debug(kwargs)
		
		user		= kwargs.get('actor')
		token		= kwargs.get('token')
		
		#create or refresh the alias
		user = levr.build_display_name(user)
		
		
		#add foursquare token
		user.foursquare_token = token
		#query foursquare for user data
		user = social.foursquare_deets(user,token)

		#update
		user.put()
		
		#return the user
		response = {'user':api_utils.package_user(user,'private')}
		api_utils.send_response(self,response,user)
		
class ConnectTwitterHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,token=True,screenName=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('CONNECT TWITTER\n\n\n')
			logging.debug(kwargs)
			
			user		= kwargs.get('actor')
			
			token		= kwargs.get('token')
			screen_name	= kwargs.get('screenName')
			
			#create or refresh the alias
			user = levr.build_display_name(user)
			
			#add twitter token
			user.twitter_token = token
			#add screen name
			user.twitter_screen_name = screen_name
			
			social.twitter_deets(user,token,screen_name)
			#update
	# 		user.put()
			
			#return the user
			response = {'user':api_utils.package_user(user,'private')}
			api_utils.send_response(self,response,user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')


app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler)],debug=True)