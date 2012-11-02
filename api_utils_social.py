from google.appengine.api import urlfetch
from google.appengine.ext import db
from social_data import * #@UnusedWildImport
import json
import levr_classes as levr
import logging
import oauth2 as oauth
import time
#import hmac
#import hashlib
#import binascii
#for twitter api


class SocialClass:
	def __init__(self, user, *args, **kwargs):
		logging.debug('init social class')
		self.user = user
		self.set_noise_level(*args)
	def set_noise_level(self,*args):
		if 'verbose' in args:
			self.verbose = True
			logging.info('\n\n\n\t\t\t RUNNING IN VERBOSE MODE \n\n\n')
		else:
			self.verbose = False
		if 'debug' in args:
			self.debug	= True
			logging.warning('\n\n\n\t\t\t\t WARNING: RUNNING IN DEBUG MODE \n\n\n')
		else: 
			self.debug = False
	def build_display_name(self, first_name, last_name):
		display_name = ''
		if first_name:
			display_name += first_name
			if last_name:
				display_name += ' ' + last_name[0]+'.'
		elif last_name:
			display_name += last_name
#		return first_name + ' ' + last_name[0] + '.'
		return display_name
	
	def first_time_connect(self, auto_put=True, *args, **kwargs):
		'''
		
		User is just connecting to levr via a social service for the first time
		Updates a users login credentials, their personal information, and their friend linkage
		
		Returns: User entity
		
		Options:
		auto_put (default: False)
			automatically puts the user entity back before returning. Still returns the user entity
		'''
		logging.debug('\n\n FISRT TIME CONNECT \n\n')
		
		#update access credentials
		self.update_credentials(*args, **kwargs)
		#update user info
		new_user_details = self.update_user_details()
		#pull user friends
		new_friends = self.update_friends()
		
		
		
		if auto_put:
			#put the user before returnsing
			user = self.put()
		else: 
			user = self.return_user()
		return user, new_user_details, new_friends

	def add_followers(self, to_be_connected):
		'''
		Takes a list of user entities, checks if they are already following the user
		If not already following, they follow and are notified
		If they are already following, nothing happens
		'''
#		#add actor to the list of followers
#		for user in to_be_connected:
#			if self.user.key() not in user.followers:
#				user.followers.append(actor)
		logging.debug('\n\n ADD FOLLOWERS \n\n')
		
		logging.debug([user.key() for user in to_be_connected])
		to_be_notified = []
		#if the user has not been stored yet, it will not have a key
		try:	actor_id = self.user.key()
		except:
			raise Exception('User does not exist in db yet. ')
			actor_id = db.Key()
		#for each user entity that has been identified as a potential new friend
		for u in to_be_connected:
			#they will be added as a follower if they are not already one and the user is not itself
			if actor_id not in u.followers and u.key() != actor_id:
				#add the actor to the list of the found users followers
				u.followers.append(actor_id)
				to_be_notified.append(u)
		
		if to_be_notified:
			logging.debug(to_be_notified)
			logging.debug(type(to_be_notified[0]))
			logging.debug([user.key() for user in to_be_notified])
			#place the list of user entities, and get a list of ids in return
			to_be_notified = db.put(to_be_notified)
#			to_be_notified = [friend.key() for friend in to_be_notified]
			
			#only notify/add follower if the user is not already following
			logging.debug(to_be_notified)
			
			#replace all of the notified users
			
			
			#add the actors friends to their list of followers
			self.user.followers.extend(to_be_notified)
			
			
			#create a notification if there are users to be notified
			if to_be_notified: levr.create_notification('newFollower', to_be_notified, self.user.key())
		else:
			pass
		logging.debug("To be notified: "+str(to_be_notified))
		logging.debug(type(to_be_notified))
		return to_be_notified
	def connect_friends(self):
		'''
		SocialClass
		Finds every user that is friends with the user on other services, automatically connects them
		Returns a list of new friends, returns their ids
		'''
		logging.debug('\n\n CONNECT FRIENDS \n\n')
		
		
		levr_friends = []
		##find the users friends and add them as connections
		#only query for services that the user has provided an id for
		
		#FOURSQUARE
		logging.debug('fs: ' + str(self.user.foursquare_id))
		if self.user.foursquare_id:
#			q = levr.Customer.all(projection=['followers']).filter('foursquare_friends',self.user.foursquare_id)
			foursquare_friends	= levr.Customer.all(keys_only=True
													).filter('foursquare_friends', self.user.foursquare_id
													).order('-foursquare_friends'
													).fetch(None)
			levr_friends.extend(foursquare_friends)
			logging.debug(foursquare_friends)
		#FACEBOOK
		logging.debug('fb: ' + str(self.user.facebook_id))
		if self.user.facebook_id:
			facebook_friends	= levr.Customer.all(keys_only=True
												).filter('facebook_friends', self.user.facebook_id
												).order('-facebook_friends'
												).fetch(None)
			levr_friends.extend(facebook_friends)
		#TWITTER BY ID
		logging.debug('twitter_id: ' + str(self.user.twitter_id))
		if self.user.twitter_id:
			twitter_friends		= levr.Customer.all(keys_only=True
													).filter('twitter_friends_by_id', self.user.twitter_id
													).order('-twitter_friends_by_id'
													).fetch(None)
			levr_friends.extend(twitter_friends)
		#TWITTER BY SCREEN NAME
		logging.debug('twitter_screen_name: ' + str(self.user.twitter_screen_name))
		if self.user.twitter_screen_name:
			twitter_friends		= levr.Customer.all(keys_only=True
													).filter('twitter_friends_by_sn', self.user.twitter_screen_name
													).order('-twitter_friends_by_sn'
													).fetch(None)
			levr_friends.extend(twitter_friends)
			logging.debug(twitter_friends)
		#EMAIL
		logging.debug('email: ' + str(self.user.email))
		if self.user.email:
			email_friends		= levr.Customer.all(keys_only=True
													).filter('email_friends', self.user.email
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
	def extend_friends(self,**kwargs):
		'''
		SocialClass
		Takes in a variable dict of lists of a users new friends. 
		Extends the users friend lists with friends that do not already exist in them
		'''
		logging.debug('\n\n\n\t\t\t EXTEND FRIENDS \n\n\n')
		facebook_friends		= kwargs.get('facebook_friends',None)
		foursquare_friends		= kwargs.get('foursquare_friends',None)
		twitter_friends_by_sn	= kwargs.get('twitter_friends_by_sn',None)
		twitter_friends_by_id	= kwargs.get('twitter_friends_by_id',None)
		#update the user with their new friends if they are not already in there
		response = {}
		if foursquare_friends:
			new_foursquare_friends = filter(lambda friend:(friend not in self.user.foursquare_friends and friend != self.user.foursquare_id), foursquare_friends)
			self.user.foursquare_friends.extend(new_foursquare_friends)
			response['new_foursquare_friends'] = new_foursquare_friends
		if facebook_friends:
			new_facebook_friends = filter(lambda friend:friend not in self.user.facebook_friends and friend != self.user.facebook_id, facebook_friends)
			self.user.facebook_friends.extend(new_facebook_friends)
			response['new_facebook_friends'] = new_facebook_friends
		if twitter_friends_by_sn:
			new_twitter_friends_by_sn = filter(lambda friend:friend not in self.user.twitter_friends_by_sn and friend != self.user.twitter_screen_name, twitter_friends_by_sn)
			self.user.twitter_friends_by_sn.extend(new_twitter_friends_by_sn)
			response['new_twitter_friends_by_sn'] = new_twitter_friends_by_sn
		if twitter_friends_by_id:
			new_twitter_friends_by_id = filter(lambda friend:friend not in self.user.twitter_friends_by_id and friend != self.user.twitter_id, twitter_friends_by_id)
			self.user.twitter_friends_by_sn.extend(new_twitter_friends_by_id)
			response['new_twitter_friends_by_id'] = new_twitter_friends_by_id
		return response
	
	def fetch(self, action):
		'''
		SocialClass
		Makes a request to an api using the url and action specified
		Returns the result json
		'''
		
		logging.debug('\n\n DEFAULT FETCH DATA \n\n')
		url, method, headers = self.create_url(action)
		logging.debug('\n\n DEFAULT FETCH DATA \n\n')
		logging.debug(url)
		response = urlfetch.fetch(
					url=url,
					method=method,
					headers=headers)
#		logging.debug(levr.log_dir(result))
#		logging.debug(result.status_code)
#		logging.debug(result.headers.data)
#		logging.debug(result.content)
		
		logging.debug(response.status_code)
		logging.debug(response.headers.data)
		logging.debug(response.content)
		if response.status_code == 200:
			#request success
			content = json.loads(response.content)
		else:
			#request failed
			try:
				content = levr.log_dict(json.loads(response.content))
				headers = levr.log_dict(response.headers.data)
			except:
				content = 'Content could not be fetched\n\n'
				headers = levr.log_dict(response.headers.data)
			raise Exception('Could Not connect:' +headers+ content)
		
		
#		content = self.handle_fetch_response(content)
		
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
	def __init__(self, user=None, *args, **kwargs):
		'''
		Foursquare
		'''
		logging.debug('\n\n\n \t\t\t INIT FOURSQUARE \n\n\n')
		#set the foursquare api version
		self.version = '20121007' #the foursquare api version
		
		if 'debug' in args:
			foursquare_token = kwargs.get('foursquare_token')
			self.foursquare_token = foursquare_token
		
		if not user:
			#user was not passed, check to make sure that the user does not already exist
			# if the user exists, pass it to SocialClass.__init__
			# otherwise, create a new user and pass it that
			foursquare_token = kwargs.get('foursquare_token')
			#make sure foursquare token was passed
			assert foursquare_token, 'Did not pass a user, so must pass foursquare_token as kwarg'
			
			#assign the foursquare_token so that self.fetch will work
			self.foursquare_token = foursquare_token
			#fetch the user info
			response = self.fetch('')
			logging.debug(levr.log_dict(response))
			#get the user id
			foursquare_id = int(response['response']['user']['id'])
			
			#search for the user by that id
			user = levr.Customer.all().filter('foursquare_id',foursquare_id).get()
#			logging.debug('\n\n\n\n \t\t\t\t USER \n\n\n\n')
			logging.debug(user)
			logging.debug(levr.log_model_props(user))
			if not user:
				logging.debug('user doesnt exist')
				#user does not exist in database - create a new one!
				user = levr.create_new_user()
			else:
				logging.debug('user exists')
			# else: user was found and we will init with that user
		
		#init all dat social stuff!
		SocialClass.__init__(self, user, *args, **kwargs)
		
		
		

	def connect_with_content(self,response_dict,auto_put=True,*args,**kwargs):
		'''
		A user has already been validated with foursquare, and we have all of their information.
		Performs the same actions as first_time_connect, but without making remote calls
		
		@param response_dict: the response dictionary from connecting with foursquare
		@type response_dict: dictionary
		'''
		logging.debug('\n\n FOURSQUARE CONNECT WITH CREDENTIALS \n\n')
		
		#parse incoming dict
		user_content = response_dict['response']['user']
		friend_groups = user_content['friends']['groups']
		friend_list = []
		for group in friend_groups:
			logging.debug(group)
			logging.debug(type(group))
			if group['count'] != 0:
				logging.debug
				friend_list.extend(group['items'])
		
		
		#update access credentials
		self.update_credentials(*args, **kwargs)
		#update user info
		new_user_details = self.update_user_details(user_content)
		#pull user friends
		new_friends = self.update_friends(friend_list)
		
		
		
		if auto_put:
			#put the user before returnsing
			user = self.put()
		else: 
			user = self.return_user()
		return user, new_user_details, new_friends
		
	def update_credentials(self, *args, **kwargs):
		'''
		Foursquare
		'''
		logging.debug('\n\n FOURSQUARE UPDATE CREDENTIALS \n\n')
		self.user.foursquare_connected		= True
		
		#grab foursquare credentials
		foursquare_token = kwargs.get('foursquare_token',None)
		#assure foursquare credentials exist
		assert foursquare_token, 'foursquare_token required in kwargs'
		
		self.user.foursquare_token	= foursquare_token
		return
		
	def update_user_details(self,content=None):
		'''
		Foursqaure
		Grabs the users personal information from foursquare and updates the user
		
		if content is passed, it should be the user dict responded by foursquare
		'''
		logging.debug('\n\n FOURSQUARE UPDATE USER DETAILS PREFETCH \n\n')
		#get foursquare details
		if not content:
			logging.debug('USER CONTENT WAS NOT PASSED... fetch data')
			foursquare_response = self.fetch('')
			content = foursquare_response['response']['user']
		else:
			logging.debug('USER CONTENT WAS PASSED... do not fetch data')
			pass
		logging.debug('\n\n FOURSQUARE UPDATE USER DETAILS POSTFETCH \n\n')
		
#		logging.debug(foursquare_response)
		
		logging.debug(levr.log_dict(content))
		logging.debug(type(content))
		#give preference to facebook and twitter info over foursquare info
		#grab stuff
		updated = {}
		
		#update the users foursquare_id
		foursquare_id	= int(content.get('id',None))
		assert foursquare_id, "foursquare_id was not retrieved"
		if not self.user.foursquare_id:
				self.user.foursquare_id	= foursquare_id
				updated['foursquare_id']= foursquare_id
		
		#update the rest of the users properties
		if not self.user.facebook_connected and not self.user.twitter_connected:
#			vals = {
#				'first_name'	: content['firstName'],
#				'last_name'		: content['lastName'],
#				'display_name'	: self.build_display_name(first_name, last_name),
#				'photo'			: content['photo']['prefix'] + '500x500' + content['photo']['suffix'],
#				'email'			: content['contact']['email'],
#				'foursquare_id'	: int(content['id'])
#				
#				}
			first_name = content.get('firstName','') #content['firstName']
			last_name	= content.get('lastName','') #content['lastName']
			display_name	= self.build_display_name(first_name, last_name)
			photo = content.get('photo',None)
			if photo:
				photo = photo.get('prefix','')+'500x500'+photo.get('suffix','')
#			photo			= content['photo']['prefix'] + '500x500' + content['photo']['suffix']
			contact = content.get('contact',None)
			if contact:
				email = contact.get('email')
#			email			= content['contact']['email']
			
			
			
			if not self.user.first_name:
				self.user.first_name	= first_name
				updated['first_name']	= first_name
			if not self.user.last_name:
				self.user.last_name		= last_name
				updated['last_name']	= last_name
			if not self.user.display_name:
				self.user.display_name	= display_name
				updated['display_name']	= display_name
#			if not self.user.photo:
			#keep photo up to date
			self.user.photo			= photo
			updated['photo']		= photo
			#grab email
			if not self.user.email:
				self.user.email			= email
				updated['email']		= email
			
			logging.debug(levr.log_model_props(self.user))
		else:
			
#			raise Exception('user has already connected with facebook or twitter')
			logging.info('user has already connected with facebook or twitter')
		return updated
	
	def update_friends(self,friends=None):
		'''
		Foursquare
		1. Makes a call to foursquare to pull all of the users friends
		2. Pulls the facebook, twitter, email, and foursquare info from each friend with that info
		3. Adds that information to a corresponding list on the user entity
		4. Creates the db linkage between user and friends by calling create_notification
		'''
		logging.debug('\n\n FOURSQUARE UPDATE FRIENDS \n\n')
		#get the users friends
		if not friends:
			logging.debug('FRIEND DATA DOES NOT EXIST... make fetch')
			content = self.fetch('friends')
			logging.debug(levr.log_dict(content))
			friends = content['response']['friends']['items']
		else:
			logging.debug('FRIEND DATA EXISTS... do not make fetch')
			logging.debug(levr.log_dict(friends))
		
		
		
		#grab all friend informations
		foursquare_friends		= []
		twitter_friends_by_sn	= []
		facebook_friends		= []
		email_friends			= []
		for f in friends:
			logging.debug(f)
			foursquare_friends.append(int(f['id']))
			contact			= f['contact']
			if 'twitter'	in contact:	twitter_friends_by_sn.append(contact['twitter'])
			if 'facebook'	in contact:	facebook_friends.append(int(contact['facebook']))
			if 'email'		in contact:	email_friends.append(contact['email'])
		
		
		logging.debug(twitter_friends_by_sn)
		logging.debug('\n\n')
		logging.debug(facebook_friends)
		logging.debug('\n\n')
		logging.debug(foursquare_friends)
		logging.debug('\n\n')
		
		
		#store the information for the users facebook friends that were just found
		self.extend_friends(
							twitter_friends_by_sn=twitter_friends_by_sn,
							facebook_friends=facebook_friends,
							foursquare_friends=foursquare_friends
							)
		
		#Create the connection between the user and their friends
		new_friends = self.connect_friends()
		return new_friends
	
	def create_url(self, action):
		'''
		Foursquare
		Creates a url to perform a specified action on the foursquares api
		'''
		logging.debug('\n\n FOURSQUARE CREATE URL \n\n')
		url = 'https://api.foursquare.com/v2/users/'
#		url += str(self.foursquare_id)
		logging.debug(action)
		
		if action:
			logging.debug('add action!')
			url += str(self.user.foursquare_id)
			url += '/' + action
			method = 'GET'
			headers = {}
		else:
			url += 'self'
			method = 'GET'
			headers = {}
			#otherwise, will not append action to the url
#		url += '?oauth_token=' + self.user.foursquare_token
#		url += '&v=' + self.version
		try: foursquare_token = self.user.foursquare_token
		except: foursquare_token = self.foursquare_token
		url += '?oauth_token={}&v={}'.format(foursquare_token,
											self.version)
		
		return url, method, headers
	
		
	def handle_fetch_response(self, content):
		'''
		Foursquare
		'''
		#handle response types
		
		### DEBUG
#		if action == 'user':
#			content = twitter_auth['example_user_info']['response']['content']
#		elif action == 'friends':
#			content = twitter_auth['example_friends']
		### DEBUG
#		logging.debug(content)
		return content

class Twitter(SocialClass):
	#These are values that identify our app
	_oauth_consumer_key		= twitter_auth['oauth_consumer_key']
	_oauth_consumer_secret	= twitter_auth['oauth_consumer_secret']
	def __init__(self, user=None, *args, **kwargs):
		'''
		Twitter
		'''
		logging.debug('\n\n\n \t\t\t INIT Twitter \n\n\n')
		self.set_noise_level(*args)
		# if user is not passed, then check if a user exists with the identity specified. if they do not exist, then create a new one
		if not user:
			#user was not passed, check to make sure that the user does not already exist
			# if the user exists, pass it to SocialClass.__init__
			# otherwise, create a new user and pass it that
			twitter_id				= int(kwargs.get('twitter_id'))
#			twitter_token			= kwargs.get('twitter_token')
#			twitter_token_secret	= kwargs.get('twitter_token_secret')
			
			#make sure necessary credentials were passed
			assert twitter_id, 'Did not pass a user, so must pass twitter_id as kwarg'
#			assert twitter_token, 'Did not pass a user, so must pass twitter_token as kwarg'
#			assert twitter_token_secret, 'Did not pass a user, so must pass twitter_token_secret as kwarg'
			
			#search for the user by that id
			user = levr.Customer.all().filter('twitter_id',twitter_id).get()
			
#			#fetch the user info
#			response = self.fetch('user')
#			logging.debug(levr.log_dict(response))
#			
			
			logging.debug(levr.log_model_props(user))
			if not user:
				logging.debug('user doesnt exist')
				#user does not exist in database - create a new one!
				user = levr.create_new_user()
			else:
				logging.debug('user exists')
			# else: user was found and we will init with that user
		
		#init all dat social stuff!
		assert user, 'User is not passed, and it is not being created'
		SocialClass.__init__(self, user, *args, **kwargs)
		
	
	def update_credentials(self,*args, **kwargs):
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
		if self.debug == True:
			logging.warning('\n\n\n\t\t\t\t WARNING: RUNNING TWITTER CONNECTION IN DEBUG MODE')
			self.user.twitter_token = twitter_auth['LevrDevr_oauth_token']
			self.user.twitter_token_secret = twitter_auth['LevrDevr_oauth_token_secret']
		else:
			#pull oauth credentials
			twitter_token = kwargs.get('twitter_token',None)
			twitter_token_secret = kwargs.get('twitter_token_secret',None)
			#assure the credentials exist
			assert twitter_token, 'twitter_token required in kwargs'
			assert twitter_token_secret, 'twitter_token_secret required in kwargs'
			#not in debug mode, values are user provided
			self.user.twitter_token			= twitter_token
			self.user.twitter_token_secret	= twitter_token_secret
			
		#updates the users id and/or screen name
		twitter_id 			= kwargs.get('twitter_id', False)
		twitter_screen_name	= kwargs.get('twitter_screen_name', False)
		#assure that the id or the screen name was passed
		if not twitter_id and not twitter_screen_name:
			raise Exception('twitter_id or twitter_screen_name required in kwargs')
		
		#one of the two is sufficient to access twitter, one or both is acceptable to update
		if twitter_id			: self.user.twitter_id			= int(twitter_id)
		if twitter_screen_name	: self.user.twitter_screen_name	= twitter_screen_name
		
		#user has the credentials needed to connect to twitter
		self.user.twitter_connected = True
		
		return

	

	def update_user_details(self):
		'''
		Twitter
		'''
		content = self.fetch('user')
		logging.debug('\n\n\t\t\t\t UPDATE USER DETAILS \n\n')
		logging.debug(levr.log_dict(content))
		updated = {}
		
		#update twitter info
		twitter_id	= content.get('id')
		screen_name	= content.get('screen_name')
		if not self.user.twitter_id:
			self.user.twitter_id	= twitter_id
			updated['twitter_id']	= twitter_id
		if not self.user.twitter_screen_name:
			self.user.twitter_screen_name	= screen_name
			updated['twitter_screen_name']	= screen_name
		
		#update general attributes
		if not self.user.facebook_connected:
			
			photo		= content.get('profile_image_url_https')
			name		= content.get('name')
			names		= name.split(' ')
			first_name	= names[0]
			last_name	= names[-1]
			display_name= self.build_display_name(first_name, last_name)
			
			#update user values if they are to be update
#			if not self.user.photo:
			#keep photo up to date
			self.user.photo			= photo
			updated['photo']		= photo
			
			if not self.user.first_name or not self.user.last_name:
				self.user.display_name	= display_name
				updated['display_name']	= display_name
			if not self.user.first_name:
				self.user.first_name	= first_name
				updated['first_name']	= first_name
			if not self.user.last_name:
				self.user.last_name		= last_name
				updated['last_name']	= last_name
			if not self.user.display_name:
				self.user.display_name	= display_name
				updated['display_name']
			
		else:
			return updated
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
		content= self.fetch('friends')
		logging.debug('\n\n\t\t\t\t UPDATE FRIENDS \n\n')
		#get the users friends
		#friends is a list of twitter ids, type: int
		twitter_friends_by_id = content['ids']
		
		#store the information for the users facebook friends that were just found
		self.extend_friends(twitter_friends_by_id=twitter_friends_by_id)
		
		#Create levr the connection between the user and their friends
		new_levr_friends = self.connect_friends()
		return new_levr_friends
	def create_url(self, action):
		logging.debug('\n\n\t\t\t\t CREATE URL \n\n')
		#base url
		endpoint = 'https://api.twitter.com/1.1'
		if action == 'friends':
			#fetching a users friends from twitter
			endpoint += '/friends/ids.json'
			method = "GET"
			params = {'user_id':self.user.twitter_id}
		elif action == 'followers':
			#fetching a users followers from twitter
			endpoint += '/followers/ids.json'
			method = "GET"
			params = {'user_id':self.user.twitter_id}
		elif action == 'user' or not action:
			#fetching a users info from twitter
			endpoint += '/users/show.json'
			method = "GET"
			try:
				params = {'user_id':self.user.twitter_id}
			except:
				params = {'user_id':self.twitter_id}
		else:
			levr.log_error()
			raise Exception('Invalid url action')
		logging.debug('url: ' + str(endpoint))
		
		headers = self.get_headers(endpoint, method, **params)
		
		#update url with request parameters
		req_url = endpoint + '?'
		for key in params:
#			req_url += str(key) + '=' + str(params[key]) + '&'
			req_url += '{}={}&'.format(key,params[key])
		#trim trailing ampersand
		req_url = req_url[:-1]
		
		
		logging.debug('\n\n{}\n{}\n{}\n\n'.format(req_url,method,headers))
		return req_url, method, headers
	def get_headers(self, url, method, **kwargs):
		'''
		Authorizes a twitter transaction using the stored oauth credentials
		Returns a headers string
		'''
		logging.debug('\n\n\t\t\t\t TWITTER GET HEADERS \n\n')
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
			url += str(key) + '=' + str(kwargs.get(key)) + '&'
		logging.debug(url)
		#remove last &
		url = url[:-1]
		# Set up instances of our Token and Consumer. The Consumer.key and 
		# Consumer.secret are given to you by the API provider. The Token.key and
		# Token.secret is given to you after a three-legged authentication.
		oauth_token = self.user.twitter_token
		oauth_token_secret = self.user.twitter_token_secret
		
		#create user and consumer token stuff
		token		=oauth.Token(key=oauth_token, secret=oauth_token_secret) #this is the user
		consumer	=oauth.Consumer(key=Twitter._oauth_consumer_key, secret=Twitter._oauth_consumer_secret) #this is us
		
		
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
#	def fetch(self, action=None):
#		'''
#		Debugging fetch for twitter. spoofs a server call.
#		Comment out this function to make a real server call
#		'''
#		logging.warning('\n\n\n\n\t\t\t\t WARNING: SPOOFING TWITTER CALL \n\n\n\n')
#		### DEBUG
#		if action == 'user':
#			content = twitter_auth['example_user_info']['response']['content']
#		elif action == 'friends':
#			content = twitter_auth['example_friends']
#		### DEBUG
#		return content
	def handle_fetch_response(self, content):
		'''
		The response handler for twitter requests
		Input: a urlfetch.fetch result object
		Return: if response is ok, the contents of the url fetch
			else, acts accordingly
		'''
#		#handle response types
#		if result.status_code == 200:
#			content = json.loads(result.content)
#		else: 
#			raise Exception('Could Not connect')
#			content = heads
#		
#		logging.debug(content)
		return content

class Facebook(SocialClass):
	'''
	Facebook
	'''
	def __init__(self, user=None, *args, **kwargs):
		'''
		Facebook
		'''
		logging.debug('\n\n\n \t\t\t INIT FACEBOOK \n\n\n')
		self.set_noise_level(*args)
		# if user is not passed, then check if a user exists with the identity specified. if they do not exist, then create a new one
		if not user:
			#user was not passed, check to make sure that the user does not already exist
			# if the user exists, pass it to SocialClass.__init__
			# otherwise, create a new user and pass it that
			facebook_token = kwargs.get('facebook_token')
			#make sure foursquare token was passed
			assert facebook_token, 'Did not pass a user, so must pass facebook_token as kwarg'
			
			#assign the foursquare_token so that self.fetch will work
			self.facebook_token = facebook_token
			#fetch the user info from facebook
			response = self.fetch('user')
			logging.debug(levr.log_dict(response))
			#get the user id from the remote api call
			facebook_id = int(response['id'])
			
			#search for the user in our db by that id
			user = levr.Customer.all().filter('facebook_id',facebook_id).get()
#			logging.debug('\n\n\n\n \t\t\t\t USER \n\n\n\n')
			logging.debug(user)
			logging.debug(levr.log_model_props(user))
			if not user:
				logging.debug('user doesnt exist')
				#user does not exist in database - create a new one!
				user = levr.create_new_user()
			else:
				logging.debug('user exists')
			# else: user was found and we will init with that user
		logging.debug(user)
		
		#init all dat social stuff!
		SocialClass.__init__(self, user, *args, **kwargs)
	def update_credentials(self, *args, **kwargs):
		'''
		Facebook
		Updates the users facebook api credentials
		
		'''
		logging.debug('\n\n\n\t\t\t\t FACEBOOK UPDATE CREDENTIALS \n\n\n')
		
		#get the twitter oauth_token and twitter oauth_token_secret
#		if self.debug == True:
#			logging.warning('\n\n\n\t\t\t\t WARNING: RUNNING TWITTER CONNECTION IN DEBUG MODE')
#			self.user.facebook_token	= facebook_auth['pat_facebook_token']
#			self.user.facebook_id		= int(facebook_auth['pat_facebook_id'])
#		else:
		#pull oauth credentials
		facebook_token = kwargs.get('facebook_token',None)
		facebook_id = kwargs.get('facebook_id',None)
		#assure the credentials exist
		assert facebook_token, 'facebook_token required in kwargs'
		#not in debug mode, values are user provided
		self.user.facebook_token	= facebook_token
		#facebook_id is not required to get info
		if facebook_id:
			facebook_id = int(facebook_id)
			self.user.facebook_id		= facebook_id
		#set connection to facebook
		self.user.facebook_connected = True
		return
	def update_user_details(self):
		'''
		Facebook
		Fetches a users information, parses it, and sets them to the user properties
		'''
		facebook_user = self.fetch('user')
		updated = {}
		logging.debug('\n\n\n\t\t\t\t FACEBOOK GET USER DETAILS \n\n\n')
#		name			= facebook_user['name']
		first_name		= facebook_user['first_name']
		last_name		= facebook_user['last_name']
		display_name	= self.build_display_name(first_name, last_name)
		photo			= facebook_user['picture']['data']['url']
		logging.debug(photo)
		facebook_id		= int(facebook_user['id'])
# 		if not pic_data['is_silhouette']:
			#picture is not a silhouette
			#grab photo url
# 			photo = pic_data['url']
		if not self.user.facebook_id:
			self.user.facebook_id = facebook_id
			updated['facebook_id'] = facebook_id
		
		if not self.user.first_name:
			self.user.first_name	= first_name
			updated['first_name']	= first_name
		if not self.user.last_name:
			self.user.last_name		= last_name
			updated['last_name']	= last_name
		if not self.user.display_name:
			self.user.display_name	= display_name
			updated['display_name']	= display_name
		#if not self.user.photo:
		self.user.photo			= photo
		updated['photo']		= photo
		
		return updated
	def update_friends(self):
		'''
		Facebook
		'''
		content = self.fetch('friends')
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK UPDATE FRIENDS \n\n\n')
		friends = content['data']
		facebook_friends = []
		for f in friends:
			facebook_friends.append(int(f['id']))
		
		#store the information for the users facebook friends that were just found
		self.extend_friends(facebook_friends=facebook_friends)
		
		#connect the user to their friends that exist on levr
		new_levr_friends = self.connect_friends()
		
		return new_levr_friends
	def create_url(self, action):
		'''
		Facebook
		'''
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK CREATE URL \n\n\n')
		url = 'https://graph.facebook.com/'
		
		#if the user has a registered facebook_id, use that. Otherwise, use me
#		try:
#			if self.user.facebook_id:
#				url+= self.user.facebook_id
#			else:
#				url+= 'me'
#		except:
#			url+= 'me'
#		
		
		if hasattr(self, 'user') and self.user.facebook_id:
			url+= str(self.user.facebook_id)
		else:
			url+= 'me'
		
		if action == 'friends':
			logging.debug('add action!')
#			url += str(self.user.facebook_id)
			url += '/' + action
			method = 'GET'
			headers = {}
		elif action == 'user':
			url += '?fields=id,name,picture.type(normal),first_name,last_name'
			method = 'GET'
			headers = {}
			#otherwise, will not append action to the url
		else:
			raise Exception('Unsupported facebook request')
		
		#add access token to the request
		if '?' not in url:	url += '?'
		else:				url += '&'
		try: facebook_token = self.user.facebook_token
		except: facebook_token = self.facebook_token
		
		url += 'access_token=' + facebook_token
		
		logging.debug(url)
		return url, method, headers
		return
	#===========================================================================
	# def fetch(self, action):
	#	'''
	#	Facebook
	#	Uncomment to spoof facebook fetch and override default
	#	
	#	@param action:
	#	@type action:
	#	'''
	#	if self.verbose: logging.debug('\n\n\n\t\t\t\t SPOOF FACEBOOK FETCH \n\n\n')
	#	return
	#===========================================================================
	def handle_fetch_response(self, content):
		'''
		Facebook
		
		@param response: response of a urlfetch
		@type response: <class 'google.appengine.api.urlfetch._URLFetchResult'>
		'''
		
		if self.verbose: logging.debug('\n\n\n\t\t\t\t FACEBOOK RESPONSE \n\n\n')
#		logging.debug(response.status_code)
#		logging.debug(response.headers.data)
#		logging.debug(response.content)
#		if response.status_code == 200:
#			#request success
#			content = json.loads(response.content)
#		else:
#			#request failed
#			try:
#				content = levr.log_dict(json.loads(response.content))
#			except:
#				content = levr.log_dict(response.headers.data)
#			raise Exception('Could Not connect:' + content)
		return content
