import json
import levr_encrypt as enc
import levr_classes as levr
import logging
import time
from google.appengine.ext import db
from google.appengine.api import urlfetch
import urllib
import hmac
import hashlib
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
#		logging.info(output)
		
	#remove final '&' and return string
	
	return output[:len(output)-1]
	
def twitter_deets(user,oauth_token,screen_name):
	#DEV - SPOOF TOKEN AND SCREEN NAME
	oauth_token='819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI'
	screen_name = 'LevrDevr'
	#build the request
	logging.info(urllib.quote('well,hi, there'))
	logging.info(str(int(time.time())))
	
	base_url = 'https://api.twitter.com/1.1/users/show.json'
	
	#this is our id
	oauth_consumer_key = 'JAu03A5jqlYddohoXI8Ng'
	
	
	
	params = {
		'oauth_consumer_key'		:	oauth_consumer_key,
		'oauth_nonce'				:	uuid.uuid4().hex,
		'oauth_signature_method'	:	'HMAC-SHA1',
		'oauth_timestamp'			:	str(int(time.time())),
		'oauth_token'				:	oauth_token,
		'oauth_version'				:	'1.0',
		'screen_name'				:	screen_name
		}
	
	
	#e.g. screen_name=SCREEN_NAME&etc..
	parameter_string = sort_and_encode_params(params)
	
	assembled = 'GET&'+urllib.quote(base_url)+'&'+urllib.quote(parameter_string)
	
	
	
	#parameter_string = urllib.quote('oauth_consumer_key')+'='+urllib.quote('JAu03A5jqlYddohoXI8Ng')+'&'+urllib.quote('oauth_nonce')+'='+urllib.quote(uuid.uuid4().hex)+'&'+urllib.quote('oauth_signature_method')+'='+urllib.quote('HMAC-SHA1')+'&'+'oauth_timestamp'+'='+urllib.quote(str(int(time.time())))+'&'+'oauth_token'+'='urllib.quote(oauth_token)+'&'+'oauth_version='		+		urllib.quote('1.0')+ '&screen_name='			+		urllib.quote(screen_name) #passed by user
	
	#parameter_string = urllib.quote('oauth_consumer_key='+ 'JAu03A5jqlYddohoXI8Ng'+'&oauth_nonce='+uuid.uuid4().hex+'&oauth_signature_method='+		'HMAC-SHA1'+ '&oauth_timestamp='		+		str(int(time.time()))+ '&oauth_token='			+		oauth_token+ '&oauth_version='		+		'1.0'+ '&screen_name='			+		screen_name)
	
	#generate the signature
	
	
	#dev spoof
	oauth_consumer_secret = 'h6Zh3T3PZphUg3Bu3UVdtK2AjHrDUWU6wJ4LDd5ec'
	oauth_token_secret='f0Rzdx8iiL58ebiyvokcf4JW2C9oSKbfJ81rwhsg'
	
	signing_key		= urllib.quote(oauth_consumer_secret)+'='+urllib.quote(oauth_token_secret)
	
	oauth_signature = hmac.new(signing_key,assembled,hashlib.sha1)
	logging.debug(oauth_signature)
	
	user_id='819972614'
	oauth_verifier='1514942'
	
	
	auth_string = ''
	

	try:
		#goto twitter
		url = 'https://api.twitter.com/1.1/users/show.json?screen_name=LevrDevr'
		result = urlfetch.fetch(url=url,headers={'Authorization':auth_string})
		logging.debug(result)
		twitter_user = json.loads(result.content)['user']
		return user
	except:
		levr.log_error()
		raise Exception('Invalid twitter response: '+result.content)


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
		