from google.appengine.api import urlfetch
from social_data import facebook_auth
import api_utils_social as social
import levr_classes as levr
import logging
import uuid
import webapp2
#import api_utils
#import jinja2
#import json
#import levr_utils
#import os
#import urllib
#import levr_encrypt as enc
#import levr_utils
#from google.appengine.ext import db


#CASES:

#1 - User checks in, we don't have that business in our database
	#Response: Hey, there are 10 offers near you (deeplink to dealResults)
	#Response: Hey, you should be the first to upload an offer (only for some types of establishments) (deeplink to deal upload)
#2 - User checks in, we have the business, we don't have any deals there
	#Response: same as above
#3 - User checks in, we have the business, we have one deal there
	#Response: Hey check out this deal! {{DEALTEXT}}(deeplink to dealDetail)
#4 - User checks in, we have the business, we have more than one deal there
	#Response: Hey, check out {{DEALTEXT}}(deeplink to dealDetail) and 5 more deals(deeplink to dealResults)


class AuthorizeBeginHandler(webapp2.RequestHandler):
	def get(self):
		try:
			logging.debug('\n\n\t\t Hit the Authorize Begin Handler \n\n')
			client_id		= facebook_auth['client_id']
			state			= uuid.uuid4()
			scope			= 'publish_actions'
			redirect_uri	= 'http://levr-production.appspot.com/facebook/authorize/complete'
			url = 'https://www.facebook.com/dialog/oauth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={scope}'.format(
														client_id = client_id, redirect_uri= redirect_uri, scope= scope, state= state)
			logging.debug(url)
			self.redirect(url)
		except Exception,e:
			levr.log_error(e)

class AuthorizeCompleteHandler(webapp2.RequestHandler):
	def get(self):
		try:
			logging.debug('Hit the Authorize Complete Handler')
			
			client_id = facebook_auth['client_id']
			client_secret = facebook_auth['client_secret']
			
			#=======================================================================
			# Fetch access_token from facebook
			#=======================================================================
			
			#check for error
			error = self.request.get('error',None)
			assert error == None, 'User denied request'
			
			state = self.request.get('state',None)
			code = self.request.get('code',None)
			logging.debug(state)
			logging.debug(code)
			
			
			redirect_uri = 'http://levr-production.appspot.com/facebook/authorize/complete'
			
			url = 'https://graph.facebook.com/oauth/access_token?client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}'.format(
																 client_id= client_id, redirect_uri= redirect_uri, client_secret= client_secret, code= code)
			
			# Fetch the access token from facebook
			result = urlfetch.fetch(url=url)
			logging.debug(result.content)
			logging.debug(type(result.content))
			logging.debug(levr.log_dir(result.content))
			
			facebook_token = result.content.split('&')[0].split('=')[1]
			logging.debug(facebook_token)
			
			
			
			#=======================================================================
			# Create User and connect them with levr
			#=======================================================================
			
			#wrap the user in the social class - creates new user if user doesnt exist
			user = social.Facebook(facebook_token=facebook_token)
			
			user,new_details,new_friends = user.first_time_connect(facebook_token=facebook_token)
			
			logging.debug(levr.log_model_props(user))
			logging.debug(levr.log_dict(new_details))
			logging.debug(levr.log_dict(new_friends))
			try:
				logging.debug(user.display_name)
				logging.debug(user.first_name)
				logging.debug(user.last_name)
				logging.debug(user.facebook_id)
			except:
				levr.log_error()
			#send the founders a text
			levr.text_notify(user.first_name + ' ' + user.last_name + ' from facebook')
			
			#set up the jinja template and echo out
	#		template = jinja_environment.get_template('templates/deal.html')
	#		self.response.out.write(template.render(template_values))
			self.response.out.write('Hooray! you are connected with levr!')
			logging.debug(levr.log_dict(user))
		except:
			levr.log_error()
			self.response.out.write('Could not connect with Facebook')


app = webapp2.WSGIApplication([
								('/facebook/authorize', AuthorizeBeginHandler),
								('/facebook/authorize/complete', AuthorizeCompleteHandler)
								],debug=True)
