#import webapp2
import os
import logging
#import jinja2
import levr_encrypt as enc
from datetime import datetime
from datetime import timedelta
#from google.appengine.ext import blobstore
from google.appengine.ext import db
#from google.appengine.ext.webapp import blobstore_handlers
from gaesessions import get_current_session
import base_62_converter as converter
from random import randint 
import geo.geohash as geohash



#def get_notifications(requester,start_date):
	

# ==== Functions ==== #
"""def loginCheck(self,strict):
	'''	for merchants
		This is a general-purpose login checking function 
		in "strict" mode (strict=True), this script will bounce to the login page if not logged in
		if strict=False, headers will be returned that indicate the user isn't logged in, but no bouncing'''
	session = get_current_session()
	logging.debug(session)
	if session.has_key('loggedIn') == False or session['loggedIn'] == False:
		if strict == True:
			#not logged in, bounce to login page
			logging.info('Not logged in. . .Bouncing!')
			self.redirect('/merchants/login')
		else:
			logging.info('Not logged in. . .Sending back headerData')
			headerData = {
				'loggedIn'	: False
			}
			return headerData
	elif session.has_key('loggedIn') == True and session['loggedIn'] == True:
		#logged in, grab the useful bits
		#this is a hack. . . forgive meeee
		uid = session['ownerID']
		
		headerData = {
			'loggedIn'	: session['loggedIn'],
			'ownerID'	: uid
			}
		#return user metadata.
		return headerData
	return"""

"""def signupCustomer(email,alias,pw):
	pw = enc.encrypt_password(pw)
	'''Check availability of username+pass, create and login if not taken'''
	#check availabilities
	q_email = levr.Customer.gql('WHERE email = :1',email)
	q_alias  = levr.Customer.gql('WHERE alias = :1',alias)
	r_email = q_email.get()
	r_alias = q_alias.get()
	
	if r_email == None and r_alias == None: #nothing found
		c 		= levr.Customer()
		c.email = email
		c.pw 	= pw
		c.alias = alias
		
		#generate random number to decide what split test group they are in
		choice = randint(10,1000)
		decision = choice%2
		if decision == 1:
			group = 'paid'
		else:
			group = 'unpaid'
		
		#set a/b test group to customer entity
		c.group = group
		
		#put
		c.put()
		return {
			'success'	:True,
			'uid'		:enc.encrypt_key(c.key().__str__()),
			'email'		:email,
			'userName'	:alias,
			'group'		:group
			}
	elif r_email != None:
		return {
			'success': False,
			'field': 'email',
			'error': 'That email is already registered. Try again!'
		}
	elif r_alias != None:
		return {
			'success': False,
			'field': 'alias',
			'error': 'That username is already registered. Try again!'
		}"""
		
"""def loginCustomer(email_or_owner,pw):
	'''This is passed either an email or a username, so check both'''
	logging.info(pw)
	pw = enc.encrypt_password(pw)
	logging.info(pw)
	logging.info(email_or_owner)
	q_email = levr.Customer.gql('WHERE email = :1 AND pw=:2',email_or_owner,pw)
	q_owner  = levr.Customer.gql('WHERE alias = :1 AND pw=:2',email_or_owner,pw)
	r_email = q_email.get()
	r_owner = q_owner.get()
	if r_email != None:
		#found user on the basis of email
		
		#automatically update last login
		r_email.put()
		return {
			'success'		: True,
			'data'			: {
								'uid'			: enc.encrypt_key(r_email.key().__str__()),
								'email'			: r_email.email,
								'userName'		: r_email.alias,
								'group'			: r_email.group
								},
			'notifications'	: r_email.get_notifications()
		}
	elif r_owner != None:
		#found user on the basis of username
		
		#automatically update last_login
		r_owner.put()
		
		return {
			'success'		: True,
			'data'			: {
								'uid'			: enc.encrypt_key(r_owner.key().__str__()),
								'email'			: r_owner.email,
								'userName'		: r_owner.alias,
								'group'			: r_owner.group
								},
			'notifications'	: r_owner.get_notifications()
		}
	else:
		return {
			'success'	: False,
			'error': 'Incorrect username, email, or password. Please try again!'
		}"""
