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
		#grab stuff
		user.first_name = foursquare_user['firstName']
		user.last_name = foursquare_user['lastName']
		user.alias = user.first_name+user.last_name[0]+'.'
		user.photo = foursquare_user['photo']['prefix']+'500x500'+foursquare_user['photo']['suffix']
		user.email = foursquare_user['contact']['email']
		logging.info(user.__dict__)
		
		return user
	except:
		raise Exception('Invalid foursquare response: '+result.content)
	
	return user

def sort_and_encode_params(params):
	#params must be a dictionary
	order = sorted(params)
	#output string
	output = ''
	
	for item in order:
		output+=urllib.quote(item)
		output+='='
		output+=params[item]
		output+='&'
#		logging.info(output)
		
	#remove final '&' and return string
	
	return output[:len(output)-1]
	
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
	
	#These are values that identify our app
	oauth_consumer_key = 'JAu03A5jqlYddohoXI8Ng'
	oauth_consumer_secret = 'h6Zh3T3PZphUg3Bu3UVdtK2AjHrDUWU6wJ4LDd5ec'
	oauth_token_secret='f0Rzdx8iiL58ebiyvokcf4JW2C9oSKbfJ81rwhsg'
	
	params = {
		#required oauth params
		'oauth_nonce'				:	oauth.generate_nonce(),
		'oauth_timestamp'			:	int(time.time()),
		'oauth_version'				:	'1.0',
		#params specified by us
		'screen_name'				:	screen_name
		}
	
	
	
	# Set up instances of our Token and Consumer. The Consumer.key and 
	# Consumer.secret are given to you by the API provider. The Token.key and
	# Token.secret is given to you after a three-legged authentication.
	token = oauth.Token(key=oauth_token, secret=oauth_token_secret) #this is the user
	consumer = oauth.Consumer(key=oauth_consumer_key, secret=oauth_consumer_secret) #this is us
	
	# Set our token/key parameters
	params['oauth_token'] = token.key
	params['oauth_consumer_key'] = consumer.key
	
	#the url to which the twitter api call is being made
	url = 'https://api.twitter.com/1.1/users/show.json'
	
	# Create our request. Change method, etc. accordingly.
	req = oauth.Request(method="GET", url=url, parameters=params)
	
	# Sign the request.
	signature_method = oauth.SignatureMethod_HMAC_SHA1()
	req.sign_request(signature_method, consumer, token)
	
	#create the url and the header
	req_url = req.to_url()
	logging.debug(req_url)
	header = req.to_header()
	
	
	
	
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
	
	if status == 200:
		#successful
		logging.debug('Authorized')
		
		if not user.twitter_id:
			user.twitter_id	= content.get('id_str')
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
		