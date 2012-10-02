import webapp2
import logging
import api_utils
import levr_classes as levr
import levr_encrypt as enc
import api_utils_social as social
import api_utils
from google.appengine.ext import db

class ConnectFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		token = self.request.get('token')
		uid	= self.request.get('uid')
		facebook_id = self.request.get('facebookID')
		#check token and uid and decrypt
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		if uid == '':
			api_utils.send_error(self,'Required parameter not passed: uid')
			return
		#decrypt uid
		try:
			uid = db.Key(enc.decrypt_key(uid))
		except:
			api_utils.send_error(self,'Invalid parameter: uid')
			return
		
		#grab user
		user = levr.Customer.get(uid)
		#add facebook token
		user.facebook_token = token
		#fetch user info from facebook graph api
		user = social.facebook_deets(user,facebook_id,token)
		
		
		#update
		user.put()
		
		#return the user
		response = {'user':api_utils.package_user(user,True)}
		api_utils.send_response(self,response,user)


class ConnectFoursquareHandler(webapp2.RequestHandler):
	def post(self):
		#RESTRICTED
		
		token = self.request.get('token')
		uid	= self.request.get('uid')
		#check token and uid and decrypt
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		if uid == '':
			api_utils.send_error(self,'Required parameter not passed: uid')
			return
		#decrypt uid
		try:
			uid = db.Key(enc.decrypt_key(uid))
		except:
			api_utils.send_error(self,'Invalid parameter: uid')
			return
		#grab user
		user = levr.Customer.get(uid)
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
	def post(self):
		#RESTRICTED
		
		token = self.request.get('token')
		uid	= self.request.get('uid')
		#check token and uid and decrypt
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		if uid == '':
			api_utils.send_error(self,'Required parameter not passed: uid')
			return
		#check screen_name
		screen_name = self.request.get('screenName')
		if screen_name == '':
			api_utils.send_error(self,'Required parameter not passed: screenName')
			return
		#decrypt uid
		try:
			uid = db.Key(enc.decrypt_key(uid))
		except:
			api_utils.send_error(self,'Invalid parameter: uid')
			return
		
		#grab user
		user = levr.Customer.get(uid)
		#add twitter token
		user.twitter_token = token
		#add screen name
		user.twitter_screen_name = screen_name
		#update
		user.put()
		
		#return the user
		response = {'user':api_utils.package_user(user,'private')}
		api_utils.send_response(self,response,user)


app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler)],debug=True)