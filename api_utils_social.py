import json
import levr_encrypt as enc
import levr_classes as levr
import logging
import time
from google.appengine.ext import db
from google.appengine.api import urlfetch
import oauth2 as oauth
import urllib
#import hmac
#import hashlib
#import binascii
#for twitter api
import uuid

def foursquare_deets(user,token):
	try:
		#goto foursquare
		url = 'https://api.foursquare.com/v2/users/self?v=20120920&oauth_token='+token
		result = urlfetch.fetch(url=url)
		foursquare_user = json.loads(result.content)['response']['user']
		
		#give preference to facebook and twitter info over foursquare info
		if not user.facebook_id and not user.twitter_id:
			#grab stuff
			user.first_name = foursquare_user['firstName']
			user.last_name = foursquare_user['lastName']
			user.alias = user.first_name+user.last_name[0]+'.'
			user.photo = foursquare_user['photo']['prefix']+'500x500'+foursquare_user['photo']['suffix']
			user.email = foursquare_user['contact']['email']
			logging.info(user.__dict__)
		else:
			logging.debug('user has already connected with facebook or twitter')
		return user
	except:
		raise Exception('Invalid foursquare response: '+result.content)
	
	return user

def authorize_twitter(url,oauth_token,*args,**kwargs):
	'''
	kwargs is reserved for params
	'''
	#These are values that identify our app
	oauth_token_secret='f0Rzdx8iiL58ebiyvokcf4JW2C9oSKbfJ81rwhsg'
	oauth_consumer_key = 'JAu03A5jqlYddohoXI8Ng'
	oauth_consumer_secret = 'h6Zh3T3PZphUg3Bu3UVdtK2AjHrDUWU6wJ4LDd5ec'
	
	
	params = {
		#required oauth params
		'oauth_nonce'				:	oauth.generate_nonce(),
		'oauth_timestamp'			:	int(time.time()),
		'oauth_version'				:	'1.0',
		}
	#extend the params dict with request specific info
	for key in kwargs:
		params[key] = kwargs.get(key)
	
	
	# Set up instances of our Token and Consumer. The Consumer.key and 
	# Consumer.secret are given to you by the API provider. The Token.key and
	# Token.secret is given to you after a three-legged authentication.
	token = oauth.Token(key=oauth_token, secret=oauth_token_secret) #this is the user
	consumer = oauth.Consumer(key=oauth_consumer_key, secret=oauth_consumer_secret) #this is us
	
	# Set our token/key parameters
	params['oauth_token'] = token.key
	params['oauth_consumer_key'] = consumer.key
	
	#the url to which the twitter api call is being made
	url = url
	
	# Create our request. Change method, etc. accordingly.
	req = oauth.Request(method="GET", url=url, parameters=params)
	
	# Sign the request.
	signature_method = oauth.SignatureMethod_HMAC_SHA1()
	req.sign_request(signature_method, consumer, token)
	
	#create the url and the header
	req_url = req.to_url()
	logging.debug(req_url)
	header = req.to_header()
	logging.debug(header)
	
	return req_url, header
def find_twitter_friends(user,*args,**kwargs):
	development = kwargs.get('development',False)
	if development:
		#### DEBUG
		#this is the twitter_token that is fetched from the phone
		oauth_token = '819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI'
		#the users twitter handler/screen name
		screen_name = 'LevrDevr'
		#### /DEBUG
	else:
		oauth_token = user.twitter_token
		screen_name = user.twitter_screen_name
	
	#the url to which the twitter api call is being made
	url = 'https://api.twitter.com/1.1/users/show.json'
#		'https://api.twitter.com/1.1/friends/ids.json',		#get the ids of friends who the user is following

	
	req_url, header = authorize_twitter(url,oauth_token,screen_name=screen_name)
	
	result = urlfetch.fetch(
				url=req_url,#+"?screen_name=LevrDevr",
				method=urlfetch.GET,
				headers=header)
#	logging.debug(levr.log_dir(result))
	content = json.loads(result.content)
	status = result.status_code
	heads = result.headers.data
	logging.debug(heads)
	logging.debug(status)
	logging.debug(content)
	
	
"""
development = kwargs.get('development',False)
	if development:
		#### DEBUG
		#this is the twitter_token that is fetched from the phone
		oauth_token = '819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI'
		#the users twitter handler/screen name
		screen_name = 'LevrDevr'
		#### /DEBUG
	else:
		raise Exception('not running development')
		oauth_token = user.twitter_token
		screen_name = user.twitter_screen_name
	
	#the urls to which the twitter api call is being made
	urls = {
#		'user_info'	:'https://api.twitter.com/1.1/users/show.json',
		'friends'	:'https://api.twitter.com/1.1/friends/ids.json'		#get the ids of friends who the user is following
#		'followers'	:'https://api.twitter.com/1.1/followers/ids.json'
		}
	results = {
#			'user_info'	:{},
			'friends'	:{}
#			'followers'	:{}
			}
	
	'''
	OAuth oauth_consumer_key="JAu03A5jqlYddohoXI8Ng", 
	oauth_nonce="928a0b9333f96e098b8e323af864c025", 
	oauth_signature="jCjfMIKPmcBlU%2BqZAVr5Z6V2poA%3D", 
#	oauth_signature_method="HMAC-SHA1", 
	oauth_timestamp="1349554039", 
	oauth_token="819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI", 
	oauth_version="1.0"
	'''
	oauth_version="1.0", 
	oauth_token="819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI", 
	oauth_nonce="84632083", 
	oauth_timestamp="1349554749", 
	oauth_signature="HsH1txawiQK62QIEuUNMQn6BU6w%3D", 
	oauth_consumer_key="JAu03A5jqlYddohoXI8Ng", 
#	oauth_signature_method="HMAC-SHA1"
	
	
	for key in urls:
		
		req_url, headers = authorize_twitter(urls[key],oauth_token,screen_name=screen_name)
		logging.debug("\n\n\n\n\n\n\n")
		logging.debug(headers)
		logging.debug("\n\n\n\n\n\n\n")
		logging.debug(req_url)
		logging.debug("\n\n\n\n\n\n\n")
		result = urlfetch.fetch(
					url=req_url+"?screen_name=LevrDevr",
					method=urlfetch.GET,
					headers=headers)
	#	logging.debug(levr.log_dir(result))
		content = json.loads(result.content)
		status = result.status_code
		heads = result.headers.data
		logging.debug(heads)
		logging.debug(status)
		logging.debug(content)
		
		
		results[key]['content']	= content
		results[key]['status']	= status
		results[key]['headers']	= heads
	logging.debug('!!!!!!!')
	logging.debug(levr.log_dict(results))

"""
def twitter_deets(user,*args,**kwargs):
	
	development = kwargs.get('development',False)
	if development:
		#### DEBUG
		#this is the twitter_token that is fetched from the phone
		oauth_token = '819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI'
		#the users twitter handler/screen name
		screen_name = 'LevrDevr'
		#### /DEBUG
	else:
		oauth_token = user.twitter_token
		screen_name = user.twitter_screen_name
	
	#the url to which the twitter api call is being made
#	url = 'https://api.twitter.com/1.1/users/show.json'
	url = 'https://api.twitter.com/1.1/friends/ids.json'
	req_url, header = authorize_twitter(url,oauth_token,screen_name=screen_name)
	###
	#UPDATE USER DATA
	###
	
	result = urlfetch.fetch(
				url=req_url+"?screen_name=LevrDevr",
				method=urlfetch.GET,
				headers=header)
#	logging.debug(levr.log_dir(result))
	content = json.loads(result.content)
	status = result.status_code
	heads = result.headers.data
	logging.debug(heads)
	logging.debug(status)
	logging.debug(content)
	
	if status == 200:
		#successful
		logging.debug('Authorized')
		
		if not user.twitter_id:
			user.twitter_id	= content.get('id')
		
		
		#check if user has connected facebook
		#defer to facebook info
		if not user.facebook_id:
			
			if user.photo == 'http://www.levr.com/img/levr.png':
				user.photo		= content.get('profile_image_url')
			
			#create users name
			name	= content.get('name')
			name = name.split(' ')
			logging.debug(name)
			if not user.first_name:
				user.first_name	= name[0]
			if not user.last_name:
				user.last_name	= name[-1]
			if not user.display_name:
				user = levr.build_display_name(user)
			logging.debug(levr.log_model_props(user))
		else:
			logging.debug('user has already connected with facebook')
		
		
	elif status == 401:
		logging.error('NOT AUTHORIZED')
		
	else:
		logging.debug('OTHER')
	
#	logging.debug(levr.log_dir(heads))
	return user
	


def facebook_deets(user,facebook_id,token,*args,**kwargs):
	try:
		#goto facebook
		url =  'https://graph.facebook.com'
		url += '/'+facebook_id
		url += '?access_token='+token
		url += '&fields=id,name,picture.type(normal),first_name,last_name'
		result = urlfetch.fetch(url=url)
		facebook_user = json.loads(result.content)
		logging.debug(facebook_user)
		logging.debug(levr.log_dict(facebook_user))
		
		if 'error' not in facebook_user:
			#successfull query
			user.facebook_id = facebook_user['id']
			name = facebook_user['name']
			user.first_name = facebook_user['first_name']
			user.last_name = facebook_user['last_name']
			#get picture
			pic_data = facebook_user['picture']['data']
			if not pic_data['is_silhouette']:
				#picture is not a silhouette
				#grab photo url
				user.photo = pic_data['url']
			
			
		else:
			raise Exception('Invalid facebook response: '+result.content)
		
		return user
	except Exception,e:
		levr.log_error(e)
		