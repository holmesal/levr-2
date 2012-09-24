import webapp2
import logging
import api_utils
import levr_classes as levr
import levr_encrypt as enc
from random import randint
from google.appengine.ext import db
from google.appengine.api import urlfetch
import json


class SignupFacebookHandler(webapp2.RequestHandler):
	def get(self):
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
			response = {'user':api_utils.package_user(existing_user,'private')}
			api_utils.send_response(self,response,existing_user)
		else:
			#user does not exist, create new and populate via facebook API
			user = levr.Customer()
			user.facebook_token = token
#			#
#			#populate with facebook stuff here
#			#
			user.put()
			response = {'user':api_utils.package_user(user,'private')}
			api_utils.send_response(self,response,user)
			

class SignupFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE foursquare_token = :1',token).get()
		
		if existing_user:
			#user already exists and is trying to log in again, return this user
			response = {'user':api_utils.package_user(existing_user,'private')}
			api_utils.send_response(self,response,existing_user)
		else:
			#user does not exist, create new and populate via foursquare API
			user = levr.Customer()
			user.foursquare_token = token
			logging.info(token)
			
			#goto foursquare
			url = 'https://api.foursquare.com/v2/users/self?v=20120920&oauth_token='+token
			result = urlfetch.fetch(url=url)
			foursquare_user = json.loads(result.content)['response']['user']
			#grab stuff
			user.first_name = foursquare_user['firstName']
			user.last_name = foursquare_user['lastName']
			user.photo = foursquare_user['photo']['prefix']+'500x500'+foursquare_user['photo']['suffix']
			user.email = foursquare_user['contact']['email']
			logging.info(user.__dict__)
			#store user
			user.put()
			response = {'user':api_utils.package_user(user,'private')}
			api_utils.send_response(self,response,user)
		
class SignupTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		
		#check if token currently exists in datastore
		existing_user = levr.Customer.gql('WHERE twitter_token = :1',token).get()
		
		if existing_user:
			#user already exists and is trying to log in again, return this user
			response = {'user':api_utils.package_user(existing_user,'private')}
			api_utils.send_response(self,response,existing_user)
		else:
			#user does not exist, create new and populate via twitter API
			user = levr.Customer()
			user.twitter_token = token
#			#
#			#populate with twitter stuff here
#			#
			user.put()
			response = {'user':api_utils.package_user(user,'private')}
			api_utils.send_response(self,response,user)
		
class SignupLevrHandler(webapp2.RequestHandler):
	def get(self):
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
		
		#put and reply
		user.put()
		response = {'user':api_utils.package_user(user,'private')}
		api_utils.send_response(self,response,user)
		
		
app = webapp2.WSGIApplication([('/api/signup/facebook', SignupFacebookHandler),
								('/api/signup/foursquare', SignupFoursquareHandler),
								('/api/signup/twitter', SignupTwitterHandler),
								('/api/signup/levr.*', SignupLevrHandler)],debug=True)