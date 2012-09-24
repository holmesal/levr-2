import webapp2
import logging
import api_utils
import levr_classes as levr
import levr_encrypt as enc
from google.appengine.ext import db

class ConnectFacebookHandler(webapp2.RequestHandler):
	def get(self):
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
		#add facebook token
		user.facebook_token = token
		#update
		user.put()
		
		#return the user
		response = {'user':api_utils.package_user(user,'private')}
		api_utils.send_response(self,response,user)


class ConnectFoursquareHandler(webapp2.RequestHandler):
	def get(self):
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
		#update
		user.put()
		
		#return the user
		response = {'user':api_utils.package_user(user,'private')}
		api_utils.send_response(self,response,user)
		
class ConnectTwitterHandler(webapp2.RequestHandler):
	def get(self):
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
		#add twitter token
		user.twitter_token = token
		#update
		user.put()
		
		#return the user
		response = {'user':api_utils.package_user(user,'private')}
		api_utils.send_response(self,response,user)


app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler)],debug=True)