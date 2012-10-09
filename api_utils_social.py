import json
import levr_encrypt as enc
import levr_classes as levr
import logging
import time
from google.appengine.ext import db
from google.appengine.api import urlfetch
import oauth2 as oauth
import urllib
from social_data import *
#import hmac
#import hashlib
#import binascii
#for twitter api
import uuid


class SocialClass:
	def __init__(self,user):
		self.user = user
		raise Exception('social class is being instanciated')

	def add_followers(self,to_be_connected):
		'''
		Takes a list of user entities, checks if they are already following the user
		If not already following, they are notified
		If they are already following, nothing happens
		'''
#		#add actor to the list of followers
#		for user in to_be_connected:
#			if self.user.key() not in user.followers:
#				user.followers.append(actor)
		logging.debug('\n\n ADD FOLLOWERS \n\n')
		
		logging.debug(to_be_connected)
		to_be_notified = []
		actor_id = self.user.key()
		for u in to_be_connected:
			if actor_id not in u.followers:
				#add the actor to the list of the found users followers
				u.followers.append(actor_id)
				to_be_notified.append(u)
		
		if to_be_notified:
			#place the list of user entities, and get a list of ids in return
			to_be_notified = db.put(to_be_notified)
#			to_be_notified = [friend.key() for friend in to_be_notified]
			
			#only notify/add follower if the user is not already following
			logging.debug(to_be_notified)
			
			#replace all of the notified users
			
			
			#add the actors friends to their list of followers
			self.user.followers.extend(to_be_notified)
			
			
			#create a notification if there are users to be notified
			if to_be_notified: levr.create_notification('newFollower',to_be_notified,self.user.key())
		else:
			pass
		return to_be_notified
	def connect_friends(self):
		'''
		Finds every user that is friends with the user on other services, automatically connects them
		Returns a list of new friends, returns their ids
		'''
		logging.debug('\n\n CONNECT FRIENDS \n\n')
		logging.debug(self.user.foursquare_id)
		levr_friends = []
		##find the users friends and add them as connections
		#only query for services that the user has provided an id for
		
		#FOURSQUARE
		logging.debug('fs: '+str(self.user.foursquare_id))
		if self.user.foursquare_id:
#			q = levr.Customer.all(projection=['followers']).filter('foursquare_friends',self.user.foursquare_id)
			foursquare_friends	= levr.Customer.all(keys_only=True
													).filter('foursquare_friends',self.user.foursquare_id
															).order('-foursquare_friends'
																).fetch(None)
			levr_friends.extend(foursquare_friends)
			logging.debug(foursquare_friends)
		#FACEBOOK
		logging.debug('fb: '+str(self.user.facebook_id))
		if self.user.facebook_id:
			facebook_friends	= levr.Customer.all(keys_only=True
												).filter('facebook_friends',self.user.facebook_id
														).order('-facebook_friends'
															).fetch(None)
			levr_friends.extend(facebook_friends)
		#TWITTER BY ID
		logging.debug('twitter_id: '+str(self.user.twitter_id))
		if self.user.twitter_id:
			twitter_friends		= levr.Customer.all(keys_only=True
													).filter('twitter_friends_by_id',self.user.twitter_id
															).order('-twitter_friends_by_id'
																).fetch(None)
			levr_friends.extend(twitter_friends)
		#TWITTER BY SCREEN NAME
		logging.debug('twitter_screen_name: '+str(self.user.twitter_screen_name))
		if self.user.twitter_screen_name:
			twitter_friends		= levr.Customer.all(keys_only=True
													).filter('twitter_friends_by_sn',self.user.twitter_screen_name
															).order('-twitter_friends_by_sn'
																).fetch(None)
			levr_friends.extend(twitter_friends)
			logging.debug(twitter_friends)
		#EMAIL
		logging.debug('email: '+str(self.user.email))
		if self.user.email:
			email_friends		= levr.Customer.all(keys_only=True
													).filter('email_friends',self.user.email
															).order('-email_friends'
																).fetch(None)
			levr_friends.extend(email_friends)
		
		#levr friends is a list of keys of all friends who have indicated connections with the actor
		logging.debug(levr_friends)
		
		#remove duplicate friends
		levr_friends = list(set(levr_friends))
		
		#get the friend entities
		levr_friends = db.get(levr_friends)
		
		#set friends as levr followers
		new_friends = self.add_followers(levr_friends)
		
		return new_friends
	def fetch(self,action):
		'''
		SocialClass
		Makes a request to an api using the url and action specified
		Returns the result json
		'''
		
		logging.debug('\n\n DEFAULT FETCH DATA \n\n')
		url, method, headers = self.create_url(action)
		logging.debug('\n\n DEFAULT FETCH DATA \n\n')
		logging.debug(url)
		result = urlfetch.fetch(
					url=url,
					method=method,
					headers=headers)
#		logging.debug(levr.log_dir(result))
#		logging.debug(result.status_code)
#		logging.debug(result.headers.data)
#		logging.debug(result.content)
		
		
		content = self.handle_fetch_response(result)
		return content
	def put(self):
		'''
		replicates the action of putting an entity back in the db
		necessary because the user exists in this class's scope
		returns the user's id
		'''
		logging.debug('\n\n PUT \n\n')
		db.put(self.user)
		return self.user
	def return_user(self):
		'''
		Simply returns the user object that exists in the scope of this class without putting it first
		Used when the user will be modified further outside of the SocialClass
		'''
		logging.debug('\n\n RETURN USER \n\n')
		return self.user

class Foursquare(SocialClass):
	def __init__(self,user,*args):
		'''
		Foursquare
		'''
		self.user				= user
		self.version = '20121007' #the foursquare api version
		if 'verbose' in args:
			self.verbose = True
	def first_time_connect(self,auto_put=True,*args,**kwargs):
		'''
		Foursquare
		User is just connecting to levr via a social service for the first time
		Updates a users login credentials, their personal information, and their friend linkage
		
		Returns: User entity
		
		Options:
		auto_put (default: False)
			automatically puts the user entity back before returning. Still returns the user entity
		'''
		logging.debug('\n\n FISRT TIME CONNECT \n\n')
		
		#update access credentials
		self.update_credentials(*args,**kwargs)
		#update user info
		new_user_details = self.update_user_details()
		#pull user friends
		new_friends = self.update_friends()
		
		
		
		if auto_put:
			#put the user before returnsing
			logging.debug('auto put: True')
			user = self.put()
		else: 
			logging.debug('auto put: False')
			user = self.return_user()
		return user,new_user_details,new_friends
	def update_credentials(self,*args,**kwargs):
		'''
		Foursquare
		'''
		logging.debug('\n\n UPDATE CREDENTIALS \n\n')
		self.user.foursquare_connected		= True
#		self.user.foursquare_id				= foursquare_id
		foursquare_token = kwargs.get('foursquare_token')
		if not foursquare_token:
			raise Exception('foursquare_token required in kwargs')
		self.user.foursquare_oauth_token	= foursquare_token
		return
		
	def update_user_details(self):
		'''
		Foursqaure
		Grabs the users personal information from foursquare and updates the user
		'''
		logging.debug('\n\n UPDATE USER DETAILS \n\n')
		#get foursquare details
		foursquare_response = self.fetch('')
#		logging.debug(foursquare_response)
		content = foursquare_response['response']['user']
		logging.debug(levr.log_dict(content))
		#give preference to facebook and twitter info over foursquare info
#		if not self.user.facebook_id and not self.user.twitter_id:
		#grab stuff
		updated = {}
		if not self.user.facebook_connected and not self.user.twitter_connected:
			
			first_name = content['firstName']
			last_name	= content['lastName']
			display_name	= first_name+" "+last_name[0]+'.'
			photo			= content['photo']['prefix']+'500x500'+content['photo']['suffix']
			email			= content['contact']['email']
			logging.debug(levr.log_dict(content['contact']))
			logging.debug('^^^^^^^^^CONTACT')
			foursquare_id	= int(content['id'])
			
			if not self.user.first_name:
				self.user.first_name	= first_name
				updated['first_name']	= first_name
			if not self.user.last_name:
				self.user.last_name		= last_name
				updated['last_name']	= last_name
			if not self.user.display_name:
				self.user.display_name	= display_name
				updated['display_name']	= display_name
			if not self.user.photo:
				self.user.photo			= photo
				updated['photo']		= photo
			if not self.user.email:
				self.user.email			= email
				updated['email']		= email
			if not self.user.foursquare_id:
				self.user.foursquare_id	= foursquare_id
				updated['id']			= foursquare_id
#			if not self.user.twitter_screen_name:
#				self.user.twitter_screen_name = 
			logging.debug(levr.log_model_props(self.user))
		else:
			raise Exception('user has already connected with facebook or twitter')
			logging.debug('user has already connected with facebook or twitter')
		return updated
	
	def update_friends(self):
		'''
		Foursquare
		1. Makes a call to foursquare to pull all of the users friends
		2. Pulls the facebook, twitter, email, and foursquare info from each friend with that info
		3. Adds that information to a corresponding list on the user entity
		4. Creates the db linkage between user and friends by calling create_notification
		'''
		logging.debug('\n\n UPDATE FRIENDS \n\n')
		#get the users friends
		friends = self.fetch('friends')
		logging.debug(levr.log_dict(friends))
		friends = friends['response']['friends']['items']
#		friends = friends['items']
		
		
		#grab all friend informations
		foursquare_friends	= []
		twitter_friends		= []
		facebook_friends	= []
		email_friends		= []
		for f in friends:
			foursquare_friends.append(int(f['id']))
			contact			= f['contact']
			if 'twitter'	in contact:
				twitter_friends.append(contact['twitter'])
			if 'facebook'	in contact:
				facebook_friends.append(int(contact['facebook']))
			if 'email'		in contact:
				email_friends.append(contact['email'])
		logging.debug(twitter_friends)
		logging.debug('\n\n')
		logging.debug(facebook_friends)
		logging.debug('\n\n')
		logging.debug(foursquare_friends)
		logging.debug('\n\n')
		logging.debug(foursquare_friends)
		logging.debug(filter(lambda friend: friend not in self.user.foursquare_friends,foursquare_friends))
		#update the user with their new friends if they are not already in there
		self.user.foursquare_friends.extend(filter(lambda friend: friend not in self.user.foursquare_friends,foursquare_friends))
		self.user.facebook_friends.extend(filter(lambda friend: friend not in self.user.facebook_friends,facebook_friends))
		self.user.twitter_friends_by_sn.extend(filter(lambda friend: friend not in self.user.twitter_friends_by_sn,twitter_friends))
		
#		logging.debug(self.user.foursquare_friends)
#		
#		self.user.foursquare_friends.extend(foursquare_friends)
#		self.user.facebook_friends.extend(facebook_friends)
#		self.user.twitter_friends		= twitter_friends
		
		#Create the connection between the user and their friends
		new_friends = self.connect_friends()
		
		return new_friends
		
	def create_url(self,action):
		'''
		Foursquare
		Creates a url to perform a specified action on the foursquares api
		'''
		logging.debug('\n\n CREATE URL \n\n')
		url = 'https://api.foursquare.com/v2/users/'
#		url += str(self.foursquare_id)
		logging.debug(action)
		
		if action:
			logging.debug('add action!')
			url += str(self.user.foursquare_id)
			url+='/'+action
			method = 'GET'
			headers = {}
		else:
			url += 'self'
			method = 'GET'
			headers = {}
			#otherwise, will not append action to the url
		url += '?oauth_token='+self.user.foursquare_token
		url += '&v='+self.version
		
		logging.debug(url)
		return url,method, headers
	
		
	def handle_fetch_response(self,result):
		'''
		Foursquare
		'''
		#handle response types
		if result.status_code == 200:
			content = json.loads(result.content)
		else: 
			raise Exception('Could Not connect:'+str(result.headers))
			content = heads
		### DEBUG
#		if action == 'user':
#			content = twitter_auth['example_user_info']['response']['content']
#		elif action == 'friends':
#			content = twitter_auth['example_friends']
		### DEBUG
		logging.debug(content)
		return content

class Twitter(SocialClass):
	def __init__(self,user,*args,**kwargs):
		self.user			= user
		
		
		#These are values that identify our app
		self.oauth_consumer_key		= twitter_auth['oauth_consumer_key']
		self.oauth_consumer_secret	= twitter_auth['oauth_consumer_secret']
		
		if 'verbose' in args:
			self.verbose=True
	def first_time_connect(self,twitter_token,twitter_token_secret,auto_put=True,*args,**kwargs):
		'''
		Twitter
		User is just connecting to levr via a social service for the first time
		Updates a users login credentials, their personal information, and their friend linkage
		
		Returns: User entity
		
		Options:
		auto_put (default: False)
			automatically puts the user entity back before returning. Still returns the user entity
		'''
		logging.debug('\n\n FISRT TIME CONNECT \n\n')
		
		#update access credentials
		self.update_credentials(twitter_token,twitter_token_secret,*args,**kwargs)
		#update user info
		new_user_details = self.update_user_details()
		#pull user friends
		new_friends = self.update_friends()
		
		
		
		if auto_put:
			#put the user before returnsing
			user = self.put()
		else: 
			user = self.return_user()
		return user,new_user_details,new_friends
	
	
	
	def update_credentials(self,oauth_token,oauth_token_secret,*args,**kwargs):
		'''
		Twitter
		Used to update the users twitter identification: 
		twitter_token
		twitter_token_secret
		if token or secret are set to 'debug', then LevrDevr data is used
		twitter_id and/or twitter_screen_name
		'''
		logging.debug('\n\n UPDATE CREDENTIALS \n\n')
		
		
		#get the twitter oauth_token and twitter oauth_token_secret
		if oauth_token == 'debug' or oauth_token_secret == 'debug':
			self.user.twitter_token = twitter_auth['LevrDevr_oauth_token']
			self.user.twitter_token_secret = twitter_auth['LevrDevr_oauth_token_secret']
		else:
			self.user.twitter_token_secret = oauth_token
			self.user.twitter_token_secret = oauth_token_secret
			
		#updates the users id and/or screen name
		twitter_id 			= kwargs.get('twitter_id',False)
		twitter_screen_name = kwargs.get('twitter_screen_name',False)
		logging.debug(twitter_id)
		logging.debug(twitter_screen_name)
		if not twitter_id and not twitter_screen_name:
			raise Exception('twitter_id or twitter_screen_name required in kwargs')
		
		#one of the two is sufficient to access twitter, one or both is acceptable to update
		if twitter_id			: self.user.twitter_id			= twitter_id
		if twitter_screen_name	: self.user.twitter_screen_name	= twitter_screen_name
		
		#user has the credentials needed to connect to twitter
		self.user.twitter_connected = True
		
		return
	def update_user_details(self):
		'''
		Twitter
		'''
		content = self.fetch('user')
		if not self.user.facebook_connected:
			twitter_id	= content.get('id')
			logging.debug(twitter_id)
			logging.debug(type(twitter_id))
			photo		= content.get('profile_image_url_https')
			screen_name	= content.get('screen_name')
			name		= content.get('name')
			names		= name.split(' ')
			first_name	= names[0]
			last_name	= names[-1]
			display_name= first_name + ' '+ last_name[0]+'.'
			
			#update user values if they are to be update
			updated = {}
			if not self.user.twitter_id:
				self.user.twitter_id	= twitter_id
				updated['twitter_id']	= twitter_id
			if not self.user.photo:
				self.user.photo			= photo
				updated['photo']		= photo
			if not self.user.twitter_screen_name:
				self.user.twitter_screen_name	= screen_name
				updated['twitter_screen_name']	= screen_name
			if not self.user.first_name or not self.user.last_name:
				self.user.display_name	= display_name
				updated['display_name']	= display_name
			if not self.user.first_name:
				self.user.first_name	= first_name
				updated['first_name']	= first_name
			if not self.user.last_name:
				self.user.last_name		= last_name
				updated['last_name']	= last_name
			
		else:
			raise Exception('User has already connected with facebook')
		
		
		#parse details
		return updated
	def update_friends(self):
		'''
		Twitter
		Updates a users friends
		Makes a request to twitter for all of the users friends on twitter
		Pulls all of their friends ids, and adds them to the users 'twitter_friends_by_id' property
		Creates levr friendships by searching for all users with the actors ids in one of their friend lists
		'''
		content = self.fetch('friends')
		logging.debug('\n\n UPDATE FRIENDS \n\n')
		#get the users friends
		#friends is a list of twitter ids, type: int
		twitter_friends = content['ids']
		
		#filter out existing friends
		new_twitter_friends = filter(lambda friend: friend not in self.user.twitter_friends_by_id,twitter_friends)
		#add new friends to the users list of twitter friends
		self.user.twitter_friends_by_id.extend(new_twitter_friends)
		
		#Create levr the connection between the user and their friends
		new_friends = self.connect_friends()
		return new_friends
	def create_url(self,action):
		logging.debug('\n\n CREATE URL \n\n')
		#base url
		endpoint = 'https://api.twitter.com/1.1'
		if action == 'friends':
			#fetching a users friends from twitter
			endpoint += '/friends/ids.json'
			method = "GET"
			params = {'screen_name':self.user.twitter_screen_name}
		elif action == 'followers':
			#fetching a users followers from twitter
			endpoint += '/followers/ids.json'
			method = "GET"
			params = {'screen_name':self.user.twitter_screen_name}
		elif action == 'user' or not action:
			#fetching a users info from twitter
			endpoint += '/users/show.json'
			method = "GET"
			params = {'screen_name':self.user.twitter_screen_name}
		else:
			levr.log_error()
			raise Exception('Invalid url action')
		logging.debug('url: '+str(endpoint))
		
		headers = self.get_headers(endpoint,method,**params)
		
		#update url with request parameters
		req_url = endpoint+'?'
		for key in params:
			req_url += str(key)+'='+params[key]+'&'
		#trim trailing ampersand
		req_url = req_url[:-1]
		
		return req_url,headers
	def get_headers(self,url,method, **kwargs):
		'''
		Authorizes a twitter transaction using the stored oauth credentials
		Returns a headers string
		'''
		logging.debug('\n\n AUTHORIZE \n\n')
		logging.debug(kwargs)
		params = {
			#required oauth params
			'oauth_nonce'				:	oauth.generate_nonce(),
			'oauth_timestamp'			:	int(time.time()),
			'oauth_version'				:	'1.0',
			}
		#add request parameters to the param dict
		#also create the url with params
		url += '?'
		for key in kwargs:
			params[key] = kwargs.get(key)
			url+= str(key)+'='+kwargs.get(key)+'&'
		logging.debug(url)
		#remove last &
		url = url[:-1]
		# Set up instances of our Token and Consumer. The Consumer.key and 
		# Consumer.secret are given to you by the API provider. The Token.key and
		# Token.secret is given to you after a three-legged authentication.
		oauth_token = self.user.twitter_token
		oauth_token_secret = self.user.twitter_token_secret
		
		#create user and consumer token stuff
		token		= oauth.Token(key=oauth_token, secret=oauth_token_secret) #this is the user
		consumer	= oauth.Consumer(key=self.oauth_consumer_key, secret=self.oauth_consumer_secret) #this is us
		
		
		# Create our request. Change method, etc. accordingly.
		req = oauth.Request(method=method, url=url, parameters=params)
		
		# Sign the request.
		signature_method = oauth.SignatureMethod_HMAC_SHA1()
		req.sign_request(signature_method, consumer, token)
		
		#create the url and the header
		req_url = req.to_url()
		logging.debug(req_url)
		headers = req.to_header()
		logging.debug(headers)
		
		#only send back the headers. The url is useless for some reason
		return headers
	def fetch(self,action=None):
		'''
		Debugging fetch for twitter. spoofs a server call.
		Comment out this function to make a real server call
		'''
		logging.warning('\n\n\n\n\t\t\t\t WARNING: SPOOFING TWITTER CALL \n\n\n\n')
		### DEBUG
		if action == 'user':
			content = twitter_auth['example_user_info']['response']['content']
		elif action == 'friends':
			content = twitter_auth['example_friends']
		### DEBUG
		return content
	def handle_fetch_response(self,result):
		'''
		The response handler for twitter requests
		Input: a urlfetch.fetch result object
		Return: if response is ok, the contents of the url fetch
			else, acts accordingly
		'''
		#handle response types
		if result.status_code == 200:
			content = json.loads(result.content)
		else: 
			raise Exception('Could Not connect')
			content = heads
		
		logging.debug(content)
		return content

class Facebook(SocialClass):
	'''
	Facebook
	'''
	def __init__(self,user,*args,**kwargs):
		self.user			= user
		if 'verbose' in args:
			self.verbose = True
	def first_time_connect(self,facebook_id,facebook_token,*args,**kwargs):
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK  \n\n\n')
		'''
		Facebook
		'''
		#update users facebook access credentials
		self.update_credentials(facebook_id, facebook_token,*args,**kwargs)
		#update user info
		new_user_details = self.update_user_details()
		#pull user friends
		new_friends = self.update_friends()
		
		return
	def update_credentials(self,facebook_id,facebook_token,*args,**kwargs):
		'''
		Facebook
		'''
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK UPDATE CREDENTIALS \n\n\n')
		return
	def update_user_details(self):
		'''
		Facebook
		'''
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK GET USER DETAILS \n\n\n')
		return
	def update_friends(self):
		'''
		Facebook
		'''
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK UPDATE FRIENDS \n\n\n')
		return
	def create_url(self):
		'''
		Facebook
		'''
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK CREATE URL \n\n\n')
		return
	def fetch(self,action):
		'''
		Facebook
		Uncomment to spoof facebook fetch and override default
		'''
		if self.verbose: logging.debug('\n\n\n\t\t\t\t SPOOF FACEBOOK FETCH \n\n\n')
		return
	def handle_fetch_response(self,action=False):
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK  \n\n\n')
		return

def authorize_twitter(url,oauth_token,*args,**kwargs):
	'''
	kwargs is reserved for params
	'''
	params = {
		#required oauth params
		'oauth_nonce'				:	oauth.generate_nonce(),
		'oauth_timestamp'			:	int(time.time()),
		'oauth_version'				:	'1.0',
		}
	#extend the params dict with request specific info
	#also create the url with params
	url += '?'
	for key in kwargs:
		params[key] = kwargs.get(key)
		url+= str(key)+'='+kwargs.get(key)+'&'
	
	#remove last &
	url = url[:-1]
	
	
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
		