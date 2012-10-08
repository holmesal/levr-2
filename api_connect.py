import webapp2
import logging
import api_utils
import levr_classes as levr
import levr_encrypt as enc
import api_utils_social as social
import api_utils
from google.appengine.ext import db

class ConnectFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,token=True,id=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
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
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

class ConnectFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,id=True,token=True,levrToken=True)#id=True
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('CONNECT FOURSQUARE\n\n\n')
			logging.debug(kwargs)
			
			user					= kwargs.get('actor')
			foursquare_token		= kwargs.get('token')
			foursquare_id			= kwargs.get('id')
			
			
			fs = social.Foursquare(user)
			response = fs.first_time_connect(foursquare_id,foursquare_token)
			
#			response = fs.get_friends()
#			response = fs.get_details()
			
			logging.debug(response)
			logging.debug(type(response))
#			#create or refresh the alias
#			user = levr.build_display_name(user)
#			
#			
#			#add foursquare token
#			user.foursquare_token = token
#			#query foursquare for user data
#			user = social.foursquare_deets(user,token)
#	
#			#update
#			user.put()
#			
#			#return the user
#			response = {'user':api_utils.package_user(user,'private')}
			api_utils.send_response(self,response,user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class ConnectTwitterHandler(webapp2.RequestHandler):
#	@api_utils.validate(None,None,user=False,token=False,screenName=False,levrToken=False)
	@api_utils.validate(None,'param',user=True,token=False,screenName=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('CONNECT TWITTER\n\n\n')
			logging.debug(kwargs)
			
			user		= kwargs.get('actor')
			oauth_token	= kwargs.get('token')
			screen_name	= kwargs.get('screenName')
			development = kwargs.get('development')
			
#			#add twitter token
			user.twitter_token = oauth_token
#			#add screen name
			user.twitter_screen_name = screen_name
#			
			user = social.twitter_deets(user,development=development)
			
			
			#update
	 		user.put()
			#return the user
			response = {'user':api_utils.package_user(user,'private')}
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class TestConnectionHandler(webapp2.RequestHandler):
	def get(self):
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
				p = social.Foursquare(pat)
				a = social.Foursquare(alonso)
				e = social.Twitter(ethan)
				
				logging.debug('\n\n\n\t\t\t PAT CONNECTS  \n\n\n')
				#pat connects with foursquare
				patch = p.first_time_connect(
									foursquare_token = pat.foursquare_token
									)
				
				logging.debug('\n\n\n\t\t\t ALONSO CONNECTS \n\n\n')
				al = a.first_time_connect(
									foursquare_token = alonso.foursquare_token
									)
				
				logging.debug('\n\n\n\t\t\t ETHAN CONNECTS \n\n\n')
				#ethan connects with twitter
				eth = e.first_time_connect(
									ethan.twitter_token,
									twitter_screen_name = ethan.twitter_screen_name
									)
				
				response = {
						'pat' : {
								'user':api_utils.package_user(patch[0],True),
								'new_details': patch[1],
								'new_friends': patch[2]
								},
						'alonso' : {
								'user':api_utils.package_user(al[0],True),
								'new_details': al[1],
								'new_friends': al[2]
								},
						'ethan'	: {
								'user':api_utils.package_user(eth[0],True),
								'new_details': eth[1],
								'new_friends': eth[2]
								},
						}
				
			method = self.request.get('method')
			if method == 'foursquare':
				fs_id = user.foursquare_id
				fs_token = user.foursquare_token
				u = social.Foursquare(user)
				user, new_user_details, new_friends = u.first_time_connect(foursquare_token=fs_token)
				response = {
						'user':api_utils.package_user(user,True),
						'new_details': new_user_details,
						'new_friends': new_friends
						}
			
			elif method == 'twitter':
				user = levr.Customer.all().filter('email','ethan@levr.com').get()
				u = social.Twitter(user)
				
				user, new_user_details, new_friends = u.first_time_connect(
									twitter_token,
									twitter_screen_name	=twitter_screen_name,
									twitter_id			=twitter_id
									)
				response = {
						'user':api_utils.package_user(user,True),
						'new_details': new_user_details,
						'new_friends': new_friends
						}
				
				
#				twitter_id = user.twitter_id
#				twitter_screen_name = user.twitter_screen_name
#				twitter_token = user.twitter_token
#				
#				u = social.Twitter(user)
#				u.update_credentials(
#									twitter_token,
#									twitter_screen_name	=twitter_screen_name,
#									twitter_id			=twitter_id
#									)
#				to_fetch = 'user'
#				url,headers = u.create_url(to_fetch)
#				content = u.fetch(to_fetch)
#				updated = u.update_user_details()
#				new_friends = u.update_friends()
#	#			logging.warning(u.user.email)
#				user = u.put()
#			
#	#			logging.debug(u.user.)
#				response = {
#						'user':api_utils.package_user(user,True),
#						'url'		: url,
#						'headers'	: headers,
#						'content'	: content,
#						'updated'	: updated,
#						'new_friends': new_friends
#	#					'new_user_details'	: new_user_details,
#	#					'new_friends'		: [str(x) for x in new_friends]
#						}
			api_utils.send_response(self,response,None)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler),
								('/api/connect/test', TestConnectionHandler)
								],debug=True)