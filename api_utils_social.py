import json
import levr_encrypt as enc
import logging
import time
from google.appengine.ext import db
from google.appengine.api import urlfetch
import urllib

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
		output+=urllib.quote(params[item])
		output+='&'
		logging.info(output)
		
	#remove final '&' and return
	
	return output[:len(output)-1]
	
'''def twitter_deets(user,token,screen_name):
	#grab token
	oauth_token = token
	#DEV - SPOOF TOKEN AND SCREEN NAME
	oauth_token='819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI'
	screen_name = 'LevrDevr'
	#build the request
	logging.info(urllib.quote('well,hi,there'))
	
	
	base_url = 'https://api.twitter.com/1.1/users/show.json'
	params = {
		'oauth_consumer_key'		:		'JAu03A5jqlYddohoXI8Ng',
		'oauth_nonce'				:		uuid.uuid4().hex,
		'oauth_signature_method'	:		'HMAC-SHA1',
		'oauth_timestamp'			:		str(int(time.time())),
		'oauth_token'				:		oauth_token,
		'oauth_version'				:		'1.0',
		'screen_name'				:		screen_name
		}
	
	parameter_string = sort_and_encode_params(params)
	
	assembled = 'GET&'urllib.quote(base_url)+'&'+urllib.quote(parameter_string)
	
	
	signing_key = urllib.quote(consumer_secret)+'&'+urllib.quote(token_secret)
	
	#parameter_string = urllib.quote('oauth_consumer_key')+'='+urllib.quote('JAu03A5jqlYddohoXI8Ng')+'&'+urllib.quote('oauth_nonce')+'='+urllib.quote(uuid.uuid4().hex)+'&'+urllib.quote('oauth_signature_method')+'='+urllib.quote('HMAC-SHA1')+'&'+'oauth_timestamp'+'='+urllib.quote(str(int(time.time())))+'&'+'oauth_token'+'='urllib.quote(oauth_token)+'&'+'oauth_version='		+		urllib.quote('1.0')+ '&screen_name='			+		urllib.quote(screen_name) #passed by user
	
	#parameter_string = urllib.quote('oauth_consumer_key='+ 'JAu03A5jqlYddohoXI8Ng'+'&oauth_nonce='+uuid.uuid4().hex+'&oauth_signature_method='+		'HMAC-SHA1'+ '&oauth_timestamp='		+		str(int(time.time()))+ '&oauth_token='			+		oauth_token+ '&oauth_version='		+		'1.0'+ '&screen_name='			+		screen_name)
	return False
	
	#generate the signature
	
	
	#dev spoof
	
	oauth_token_secret='f0Rzdx8iiL58ebiyvokcf4JW2C9oSKbfJ81rwhsg'
	user_id='819972614'
	oauth_verifier='1514942'
	
	
	
	

	try:
		#goto twitter
		url = 'https://api.twitter.com/1.1/users/show.json?screen_name=LevrDevr'
		result = urlfetch.fetch(url=url)
		twitter_user = json.loads(result.content)['user']
		return user
	except:
		raise Exception('Invalid twitter response: '+result.content)'''


def facebook_deets(user,token):
	try:
		#goto facebook
		url = ''+token
		result = urlfetch.fetch(url=url)
		
		return user
	except:
		raise Exception('Invalid facebook response: '+result.content)