import webapp2
import logging
import api_utils
import api_utils_social as social
import levr_classes as levr
import levr_encrypt as enc
from random import randint
from google.appengine.ext import db
import json


class SignupFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteToken=True,remoteID=True)
	def post(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE facebook_token = :1',token).get()
		
		if existing_user:
			#user already exists and is trying to log in again, return this user
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			api_utils.send_response(self,response,existing_user)
		else:
			#user does not exist, create new and populate via facebook API
			user = levr.Customer()
			user.facebook_token = token
			logging.info(token)
			
			#grab foursquare deets
			user = social.facebook_deets(user,token)
			
			#create or refresh the alias
			user = levr.build_display_name(user)
			
			user.put()
			response = {'user':api_utils.package_user(user,True,send_token=True)}
			api_utils.send_response(self,response,user)
			

class SignupFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteToken=True)#id=True
	def post(self):
		try:
			#check token
			foursquare_token = self.request.get('remoteToken',None)
			
			user = levr.Customer.all().filter('foursquare_token').get()
			
			if user:
				response = {
						'user':api_utils.package_user(user,True,send_token=True)
						}
			else:
				#create new user
				new_user = levr.Customer()
				#grab the new users foursquare info
				user = social.Foursquare(new_users)
				try:
					user, new_user_details, new_friends = user.first_time_connect(
													facebook_id = facebook_id,
													facebook_token	= facebook_token,
													)
				except Exception,e:
					assert False, 'Could not connect with foursquare, {}'.format(e)
				#return the user
				response = {
						'user':api_utils.package_user(user,True,send_token=True),
						'new_friends'		: [enc.encrypt_key(f) for f in new_friends],
						'new_user_details'	: new_user_details
						}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error('{}'.format(e))
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class SignupTwitterHandler(webapp2.RequestHandler):
	def post(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		#check everything else
		
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE twitter_token = :1',token).get()
		
		if existing_user:
			#user already exists and is trying to log in again, return this user
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			api_utils.send_response(self,response,existing_user)
		else:
			#user does not exist, create new and populate via twitter API
			user = levr.Customer()
			user.twitter_token = token
			user.twitter_screen_name = screen_name
			#user.alias = screen_name
			
			'''#grab twitter deets
			user = social.twitter_deets(user,token,screen_name)'''
			
			#create or refresh the alias
			user = levr.build_display_name(user)
			
			user.put()
			response = {'user':api_utils.package_user(user,True,send_token=True)}
			api_utils.send_response(self,response,user)
		
class SignupLevrHandler(webapp2.RequestHandler):
	def post(self):
		#RESTRICTED
		
		logging.info(self.request.get('email'))
		logging.info(self.request.get('alias'))
		logging.info(self.request.get('pw'))
		
		email = self.request.get('email')
		if email == '':
			api_utils.send_error(self,'Required parameter not passed: email')
			return
		
		alias = self.request.get('alias')
		if alias == '':
			api_utils.send_error(self,'Required parameter not passed: alias')
			return
		
		pw = self.request.get('pw')
		if pw == '':
			api_utils.send_error(self,'Required parameter not passed: pw')
			return
		
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
		user 		= levr.Customer()
		user.email = email
		user.pw 	= enc.encrypt_password(pw)
		user.alias = alias
		
		#generate random number to decide what split test group they are in
		choice = randint(10,1000)
		decision = choice%2
		if decision == 1:
			group = 'paid'
		else:
			group = 'unpaid'
		
		#set a/b test group to customer entity
		user.group = group
		
		#create or refresh the alias
		user = levr.build_display_name(user)
		
		#put and reply
		user.put()
		response = {'user':api_utils.package_user(user,True,send_token=True)}
		api_utils.send_response(self,response,user)
		
		
app = webapp2.WSGIApplication([('/api/signup/facebook', SignupFacebookHandler),
								('/api/signup/foursquare', SignupFoursquareHandler),
								('/api/signup/twitter', SignupTwitterHandler),
								('/api/signup/levr.*', SignupLevrHandler)],debug=True)