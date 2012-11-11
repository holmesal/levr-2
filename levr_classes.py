from common_word_list import blacklist
from datetime import datetime, timedelta
from google.appengine.api import taskqueue, memcache
from google.appengine.ext import blobstore, db
from google.appengine.ext.db import polymodel
from lib.nltk.stem.porter import PorterStemmer
from lib.nltk.tokenize.regexp import WhitespaceTokenizer
from math import floor, sqrt
import base_62_converter as converter
import geo.geohash as geohash
import json
import levr_encrypt as enc
import logging
import os
import promotions as promo
import random
import re
import string
import sys
import traceback
import uuid
#from random import randint
#from math import floor


#from gaesessions import get_current_session

# ==== Variables ==== #
if os.environ['SERVER_SOFTWARE'].startswith('Development') == True:
	#we are on the development environment
	URL = 'http://localhost:8080'
	development = True
else:
	#we are deployed on the server
	URL = 'http://www.levr.com'
	development = False
# FUNCTIONS
def deprecated(handler_method):
	'''
	Decorator used to warn the coder that the function they are using is deprecated
	'''
	
	def call(*args,**kwargs):
		logging.warning('Call to deprecated function: {}'.format(handler_method.__name__))
		handler_method(*args,**kwargs)
	return call
def build_display_name(user):
	'''Goes through cases of semi-populated user information from best to worst and updates display name.
	To be used when the user is created, and every time an account is connected'''
	
	if user.first_name != '' and user.last_name != '':
		user.display_name = user.first_name + ' ' + user.last_name[0] + '.'
	elif user.alias != '':
		user.display_name = user.alias
	else:
		user.display_name = 'Clint Eastwood'
	
	return user
	
upvote_phrases = [
		'Has liked your deal. Hooray!',
		'Is rushing to redeem your deal at this very moment.',
		'Thinks that your deal is just grand!',
		'Thinks your deal is absolutely spiffing.'
		]

def create_new_user(**kwargs):
	'''
	A wrapper function to create a new user. performs basic operations like creating a levr token
	and performing the initial level check
	puts the user before returning, because otherwise level check will not work
	'''
	user = Customer(levr_token=create_levr_token())
	for key in kwargs:
		setattr(user, key, kwargs.get(key))
	user.put()
	user = level_check(user)
	user.put()
	return user
def create_new_business(business_name,vicinity,geo_point,types,phone_number=None,**kwargs):
	'''
	Creates a new business entity with an optional owner.
	Puts the business before returning
	
	@type business_name: str
	@type vicinity: str
	@type geo_point: db.GeoPt
	@type types: list
	
	@keyword owner: the owner of the business
	@type owner: Customer
	'''
	if type(geo_point) == str:
		geo_point = geo_converter(geo_point)
	assert type(geo_point) == db.GeoPt, 'Must pass geo_point as a db.GeoPt property'
	assert type(types) == list, 'Must pass types as a list'
	
	
	business = Business(
					business_name = business_name,
					vicinity = vicinity,
					geo_point = geo_point,
					types = types
					)
	
	if phone_number:
		business.phone = phone_number
	
	owner = kwargs.get('owner',None)
	if owner:
		business.owner = owner
	
	
	
	business.put()
	
	return business
	
def level_check(user):
	'''updates the level of a user. this function should be run after someone upvotes a user or anything else happens.'''
	'''square root for the win'''
	old_level = user.level

	new_level = int(floor(sqrt(user.karma)))
	logging.info('{} != {}: {}'.format(old_level,new_level,str(old_level != new_level)))
	if new_level != old_level:
		logging.info('I am here!')
		#level up notification
		create_notification('levelup',user.key(),user.key(),new_level=new_level)
	user.new_notifications += 1
	user.level = new_level
		
	return user
def create_notification(notification_type,to_be_notified,actor,deal=None,**kwargs):
	'''
	notification_type	= choices: 
	'thanks',
	'favorite', 
	'followerUpload', 
	'newFollower', 
	'levelup'
	'expired'
	deprecated: redemption
	
						The action being performed
	to_be_notified		= [db.Key,db.Key,db.Key,...]
						The people or entities to be notified of this action
	deal				= db.Key
						The deal in question
	actor				= db.Key
						The person performing the action
	'''
	#===========================================================================
	# If this fundamentally changes, remember to change the undead ninja activity
	#===========================================================================
	try:
		#type cast to_be_notified as a list
		if type(to_be_notified) != list:
			#to_be_notified is not a list, make it one
			#this allows to_be_notified to be passed as a single value
			to_be_notified = [to_be_notified]
		
		
		
		if notification_type == 'newFollower':
			#user is the person that is being followed
			user = Customer.get(to_be_notified[0])
			
			#set the phrase
			line2 = 'Has subscribed to your offers.'
			
			#increment the number of notifications
			user.new_notifications += 1
			
			#replace user
			db.put(user)
		elif notification_type == "followedUpload":
			logging.info('followedUpload')
			#user is the person being notified
			users = db.get(to_be_notified)
			
			#set the phrase
			line2 = 'has uploaded a new offer.'
			
			#increment the number of notifications
			for user in users:
				user.new_notifications += 1
			
			#replace user
			db.put(users)
			
		elif notification_type == 'favorite':
			#get actor
			user = db.get(to_be_notified[0])
			#check deal is not already favorited
			# if deal not in actor_entity.favorites:
# 				actor_entity.favorites.append(deal)
# 			else:
# 				#do nothing
# 				return True
			
			
			#select a random phrase
			line2 = random.choice(upvote_phrases)
			
			#update notification count
			user.new_notifications += 1
			
			#replace users
			db.put(user)
			
			
# 		elif notification_type == 'upvote':
# 			#get user,actor
# 			[user,actor_entity,d] = db.get([to_be_notified[0],actor,deal])
# 			#make sure not already in upvotes
# 			if deal not in actor_entity.upvotes:
# 				
# 			#check actor has not redeemed yet
# 			# if d.is_exclusive:
# # 				#deal can only be redeemed once
# # 				if deal not in actor_entity.upvotes:
# # 					#actor.upvotes.append(deal)
# # 				else:
# # 					#do nothing
# # 					return True
# 			#update notification count
# 			user.new_notifications += 1
# 			
# 			#replace users
# 			db.put([user,actor_entity])
			
		elif notification_type == 'levelup':
			#get user,actor
			user = db.get(to_be_notified[0])
			
			#increment notification count
			user.new_notifications += 1
			
			new_level = kwargs.get('new_level')
			assert new_level,'Must pass new_level as kwarg to create new levelup notification'
			#write line2
			line2 = 'Good work! You are now Level {}.'.format(new_level)
			logging.info(line2)
			#replace user
			user.put()
		elif notification_type == 'expired':
			logging.debug('\n\n\n\n\n\n EXPIRED!!! \n\n\n\n')
			user = db.get(to_be_notified[0])
			
			user.new_notifications += 1
			
			line2 = 'Your deal has expired :('
			
			user.put()
			
		else:
			#users = the people to be notified
			users = Customer.get(to_be_notified)
			
			for user in users:
				if user:
					user.new_notifications += 1
			
			#replace users in db
			db.put(users)
#		else:
#			raise Exception('notification_type not recognized in create_notification')
#		
		#create and put the notification
		notification = Notification(
										notification_type	= notification_type,
										line2				= line2,
										to_be_notified		= to_be_notified,
										actor				= actor,
										deal				= deal, #default to None,
										date_in_seconds		= long(unix_time(datetime.now()))
										)
		notification.put()
		logging.debug(log_model_props(notification))
		
	except Exception,e:
		log_error(e)
		return False
	else:
		return True


def geo_converter(geo_str):
	'''
	Converts a geopoint in form := "<float>,<float>" to type db.GeoPt
	@param geo_str: a geo point in string form
	@type geo_str: str
	@return: The geopoint in form:= db.GeoPt
	@rtype: db.GeoPt
	'''
	try:
		lat, lng = geo_str.split(',')
		return db.GeoPt(lat=float(lat), lon=float(lng))
	except Exception,e:
		log_error(e)
		raise TypeError('lat,lon: '+str(geo_str))

def _convert_geo_point_to_prefixes(geo_point):
	'''
	Converts an entity of type == db.GeoPt or type == str
		to a list of geo_hash prefixes
	@param geo_point: the geopoint in question
	@type geo_point: str or db.GeoPt
	@return: a list of geohash prefixes
	@rtype: list
	'''
	# if the geohash is in string form, convert to db.GeoPt
	if type(geo_point) == str:
		geo_point = geo_converter(geo_point)
	# assure that the geopoint is the right type
	assert type(geo_point) == db.GeoPt, \
		'geo_point must be type == db.GeoPt or str: '+str(geo_point)+'; '+str(type(geo_point))
	# create the base geo_hash
	precision = 8
	geo_hash = geohash.encode(geo_point.lat, geo_point.lon, precision)
	# parse the geo_hash into prefixes
	return _convert_geohash_to_prefixes(geo_hash)
	
	
def _convert_geohash_to_prefixes(geo_hash):
	'''
	Takes a geohash, and converts it to a list of geohash prefixes
	The list of prefixes is 
	@param geo_hash: a geohash
	@type geo_hash: str
	@return: a list of geohash prefixes
	@rtype: list
	'''
	# will not store prefixes that are shorter than the min_prefix
	min_prefix = 4
	max_prefix = 7
	# create a bound on the number of prefixes we will store
	length = geo_hash.__len__()
	if length > max_prefix:
		length = max_prefix
	# constrain the parameters
	assert length >min_prefix, \
		'geo_hash length must be greater than {}'.format(min_prefix)
	# create the prefixes from the geo_hash
	prefixes = [geo_hash[:i] for i in range(min_prefix,length)]
	logging.debug(prefixes)
	return prefixes

def tagger(text): 
	# text is a string
#	parsing function for creating tags from description, etc
	#replace commas with spaces
#	text = text.replace(","," ")
#	#replace underscores with spaces
#	text = text.replace("_"," ")
#	text = text.replace("/"," ")
#	#remove all non text characters
#	text = re.sub(r"[^\w\s]", '', text)
#	#parse text string into a list of words if it is longer than 2 chars long
#	tags = [w.lower() for w in re.findall("[\'\w]+", text)]# if len(w)>2]
#	#remove redundancies
#	tags = list(set(tags))
#	#remove unwanted tags
#	filtered_tags = []
#	for tag in tags:
#		if tag.isdigit() == False:
#			#tag is not a number 
#			if tag not in blacklist:
#				filtered_tags.append(tag)
#	
#	return filtered_tags
	return create_tokens(text)


def create_tokens(text,stemmed=True,filtered=True):
	'''
	Used to create a list of indexable strings from a single multiword string
	Tokenizes the input string, and then stems each of the tokens
	Also converts each token to lowercase
	@param text: the text to be converted
	@type text: str
	@param filtered: Determines whether or not the tokens should be filtered
	@type filtered: bool
	@return: a list of tokenized and stemmed words
	@rtype: list
	'''
	tokens = _tokenize(text)
	if filtered:
		tokens = _filter_stop_words(tokens)
	if stemmed:
		tokens = _stem(tokens)
	return list(set(tokens))
def _tokenize(text):
	'''
	Tokenizes an input string
	Replaces certain delimeters with spaces, and removes punctuation
	@param text: A string composed of at least one word
	@type text: str
	@return: A list of tokenized words
	'''
	# remove unicode characters
	if type(text) == unicode:
		logging.info(text)
		text = text.encode('ascii','ignore')
		logging.info(text)
		str(text)
#	text = str(text)
#	assert type(text) == str, 'input must be a string; type: {}'.format(type(text))
	# a list of chars that will be replaced with spaces
	excludu = ['_','/',',','-','|']

	# remove punctuation
	for punct in string.punctuation:
		if punct not in excludu:
			text = text.replace(punct,'')
	
	# replace special chars with spaces
	for character in excludu:
		text = text.replace(character,' ')
	
	# tokenize the mofo!
	tokenizer = WhitespaceTokenizer()
	
	# create tokens
	return [token.lower() for token in tokenizer.tokenize(text)]
def _stem(tokens):
	'''
	Creates stemmed versions of words in a tokenized list
	@param tokens: A tokenized list of words
	@type tokens: list
	@return: A list of stem words
	@rtype: list
	'''
	stemmer = PorterStemmer()
	return [stemmer.stem(token) for token in tokens]
def _filter_stop_words(tokens):
	'''
	Filters a list of strings
	@param word_list: A tokenized, but not stemmed word list
	@type word_list: list
	@return: a list of words without stop words
	@rtype: list
	'''
	return filter(lambda x: x.isdigit() == False \
				and x not in blacklist,tokens)


def log_error(message=''):
	#called by: log_error(*self.request.body)
	exc_type,exc_value,exc_trace = sys.exc_info()
	logging.error(exc_type)
	logging.error(exc_value)
	logging.error(traceback.format_exc(exc_trace))
	logging.error(message)

def log_model_props(model,props=None):
	#returns a long multiline string of the model in key: prop
	delimeter = "\n\t\t"
	log_str = delimeter
	try:
		if type(props) is list:
			#only display certain keys
			for key in props:
				log_str += str(key)+": "+str(getattr(model,key))+delimeter
		else:
			#display all keys
			key_list = []
			for key in model.properties():
				key_list.append(key)
			key_list.sort()
			for key in key_list:
				log_str += str(key)+": "+str(getattr(model,key))+delimeter
	except Exception,e:
		logging.info('There was an error in log_model_props %s',e)
	finally:
		return log_str

def log_dir(obj,props=None):
	#returns a long multiline string of a regular python object in key: prop
	delimeter = "\n\t\t"
	log_str = delimeter
	try:
		if type(props) is list:
#			logging.debug('log some keys')
			#only display certain keys
			key_list = []
			for key in props:
				key_list.append(key)
			key_list.sort()
			for key in key_list:
				log_str += str(key)+": "+str(getattr(obj,key))+delimeter
		else:
#			logging.debug('log all keys')
			#display all keys
			for key in dir(obj):
				log_str += str(key)+": "+str(getattr(obj,key))+delimeter
	except:
		logging.info('There was an error in log_dir')
	finally:
		return log_str

def log_dict(obj,props=None,delimeter= "\n\t\t"):
	#returns a long multiline string of a regular python object in key: prop
#	delimeter = "\n\t\t"
	log_str = delimeter

	try:
		if type(props) is list:
			#only display certain keys
			for key in props:
				if type(obj[key]) == dict:
					log_str += str(key)+": "+ log_dict(obj[key],None,delimeter+'\t\t')+delimeter
				else:
					log_str += str(key)+": "+str(obj[key])+delimeter
		else:
			#display all keys
			key_list = []
			for key in obj:
				key_list.append(key)
			key_list.sort()
			for key in key_list:
				if type(obj[key]) == dict:
					log_str += str(key)+": "+ log_dict(obj[key],None,delimeter+'\t\t')+delimeter

				else:
					log_str += str(key)+": "+str(obj[key])+delimeter
	except Exception,e:
		logging.info('There was an error in log_dict %s',e)
	finally:
		return log_str
	

def create_levr_token():
	#creates a unique id than forms the levr_token
	token = uuid.uuid4()
	token = enc.encrypt_key(''.join(token.__str__().split('-'))).replace('=','')
	return token
	
def create_content_id(service):
	token = uuid.uuid4().hex
	return service[0:3]+token


def create_unique_id():
	#create the share ID - based on milliseconds since epoch
	milliseconds = int(unix_time(datetime.now()))
	#make it smaller so we get ids with 5 chars, not 6
	shortened_milliseconds = milliseconds/10 % 1000000000
	unique_id = converter.dehydrate(shortened_milliseconds)
	return unique_id

def unix_time(dt):
	epoch = datetime.utcfromtimestamp(0)
	delta = dt - epoch
	return delta.total_seconds()
	
def unix_time_millis(dt):
	return unix_time(dt) *1000.0
	
def text_notify(user_string):
	task_params = {
		'user_string'	:	user_string
	}
	logging.debug(user_string)
	taskqueue.add(url='/tasks/newUserTextTask',payload=json.dumps(task_params))


MEMCACHE_ACTIVE_GEOHASH_NAMESPACE = 'active_geohash'
MEMCACHE_TEST_GEOHASH_NAMESPACE = 'test_geohash'
def remove_memcache_key_by_deal(deal):
	'''
	Removes the memcache key that refers to the deal
	
	@warning: If expiring or rejecting a deal, call this function BEFORE
		changing the status from active or test. Otherwise, this will
		default to the active namespace, and that will probably confuse you
		if you are in the test namespace and forget about it.
	
	@param deal: The deal whos memcache entry will be deleted
	@type deal: Deal
	'''
	if deal.deal_status == DEAL_STATUS_ACTIVE:
		namespace = MEMCACHE_ACTIVE_GEOHASH_NAMESPACE
	elif deal.deal_status == DEAL_STATUS_TEST:
		namespace = MEMCACHE_TEST_GEOHASH_NAMESPACE
	else:
		raise Exception('Invalid memcache namespace: '+repr(deal.deal_status))
	logging.debug('Updating memcache')
	logging.info('updating memcahce')
	return remove_memcache_key_by_geo_point(deal.geo_point,namespace)
	
def remove_memcache_key_by_geo_point(geo_point,namespace):
	'''
	Updates the geohash+deal_key memcache when one of the geohashes has been updated and the memcache now has stale information
	Typical use case: a new deal was uploaded and the memcache key (i.e. the new deals geohash) needs to be updated
	or deleted.
	@param geo_point: the geopoint of the deal
	@type geo_point: db.GeoPt
	@param namespace: the memcaches namespace
	@type namespace: MEMCACHE_ACTIVE_GEOHASH_NAMESPACE or MEMCACHE_TEST_GEOHASH_NAMESPACE
	'''
	geo_hash_6 = geohash.encode(geo_point.lat,geo_point.lon,precision=6)
	geo_hash_5 = geohash.encode(geo_point.lat, geo_point.lon, precision=5)
	geo_hash_list = [geo_hash_5,geo_hash_6]
	logging.info(geo_hash_list)
	#create the client
	client = memcache.Client() #@UndefinedVariable
	#safely update the memcache - while loop allows this to happen all over the place psuedo-concurrently
	failsafe = 0
	while True and failsafe <50:
		failsafe +=1
		logging.debug('failsafe: '+str(failsafe))
		if client.delete_multi(geo_hash_list, namespace=namespace):
			logging.debug('geohashes {} were deleted from memcache'.format(geo_hash_list))
			break
	return

def dealCreate(params,origin,upload_flag=True,**kwargs):
	'''
	
	@param params:
	@type params:
	@param origin:
	@type origin:
	@param upload_flag:
	@type upload_flag:
	
	@keyword expires: sets the expiration on a deal. If a merchant uploads,
	  expiration can be passed as 'never' and the deal will never expire
	
	'''
	logging.debug('DEAL CREATE')
	
	logging.debug("origin: "+str(origin))
	logging.debug(log_dict(params))
	
	
	logging.debug("image was uploaded: "+str(upload_flag))
	#init tags list for deal
	tags = []
	
	#business information - never create business unless old phone
		#just want to get tags to store on deal
	#get deal information
	#create deals with appropriate owners
	
	#==== deal information ====#
	
	
	#===========================================================================
	# #==== business stuff ====#
	#===========================================================================
	if origin == 'phone_new_business':
		#The business to which a deal is being uploaded is not targeted
		logging.debug('origin is phone, new business being added')
		
		
		#business name
		if 'business_name' in params:
			business_name = params['business_name']
			logging.debug("business name: "+str(business_name))
		else:
			raise Exception('business_name not in params')
		#geo point
		
		if 'geo_point' in params:
			geo_point = params['geo_point']
			logging.debug("geo point: "+str(geo_point))
			#create geohash from geopoint
			geo_hash = geohash.encode(geo_point.lat,geo_point.lon)
		else:
			raise Exception('geo_point not in params')
		
		#vicinity
		if 'vicinity' in params:
			vicinity = params['vicinity']
			logging.debug("vicinity: "+str(vicinity))
		else:
			raise Exception('vicinity not in params')
		
		
		#types
		if 'types' in params:
			types = params['types']
			types = tagger(types)
		else:
			raise KeyError('types not in params')
		#check if business exists - get businessID
		business = Business.all().filter('business_name =',business_name).filter('vicinity =',vicinity).get()
		logging.debug('start business info')
		logging.debug(log_model_props(business))
		logging.debug('end business info')
		
		if not business:
			logging.debug('business doesnt exist')
			#if a business doesn't exist in db, then create a new one
			business = Business()
			logging.debug(log_model_props(business))
			
			
			
			#add data to the new business
			business.business_name 	= business_name
			business.vicinity 		= vicinity
			business.geo_point		= geo_point
			business.types			= types
			business.geo_hash		= geo_hash
			
			#put business
			business.put()
			
			#fire off a task to check the foursquare similarity
			task_params = {
				'geo_str'		:	str(business.geo_point),
				'query'			:	business.business_name,
				'key'			:	str(business.key())
			}
			
			#if no foursquare business exists in the database, this should try to find a foursquare business and transfer information to it
			#what if there is already a foursquare business in the database?
			
			taskqueue.add(url='/tasks/businessHarmonizationTask',payload=json.dumps(task_params))
			
			
		else:
			logging.debug('business exists')
			#business exists- grab its tags
		
		
		#grab the businesses tags
		tags.extend(business.create_tags())
		#get businessID - not encrypted - from database
		businessID = business.key()
		logging.debug("businessID: "+str(businessID))
		
		#Create tags
		
		logging.debug('-------------------------------------------')
		logging.debug(tags)
	elif origin == 'phone_merchant':
		logging.info('phone_merchant, so do not create new business')
		business = params['business']
		tags.extend(business.create_tags())
		
		#grab all the other information that needs to go into the deals
		businessID		= str(business.key())
		business_name 	= business.business_name
		geo_point		= business.geo_point
		vicinity		= business.vicinity
		geo_hash		= business.geo_hash
	else:
		#BusinessID was passed, grab the business
		logging.debug('not oldphoone')
		
		if 'business' in params:
			businessID = params['business']
			businessID	= enc.decrypt_key(businessID)
			businessID	= db.Key(businessID)
			business	= Business.get(businessID)
		else:
			raise KeyError('business not passed in params')
		#get the tags from the business
		tags.extend(business.create_tags())
		
		#grab all the other information that needs to go into the deals
		business_name 	= business.business_name
		geo_point		= business.geo_point
		vicinity		= business.vicinity
		geo_hash		= business.geo_hash
		

	logging.debug('!!!!!')
	#===========================================================================
	# #====Deal Information Lines ====#
	#===========================================================================
	#deal line 1
	if 'deal_line1' in params:
		deal_text	= params['deal_line1'].decode()
		tags.extend(tagger(deal_text))
	else:
		raise KeyError('deal_line1 not passed in params')
	
	#deal line 2
	if origin != 'phone_existing_business' and origin != 'phone_new_business':
		if 'deal_line2' in params:
			secondary_name = params['deal_line2']
		else:
			secondary_name = False
		logging.debug(secondary_name)
		if secondary_name:
			#deal is bundled
			logging.debug('deal is bundled')
			tags.extend(tagger(secondary_name))
			logging.info(tags)
			deal_type = 'bundle'
		else:
			#deal is not bundled
#			'deal is NOT bundled'
			deal_type = 'single'
	else:
		#phone uploaded deals do not pass deal_line2
		deal_type = 'single'
	
	#description
	if 'deal_description' in params:
		description = params['deal_description'].decode()
		#truncate description to a length of 500 chars
		description = description[:500]
		tags.extend(tagger(description))
	else:
		raise KeyError('deal_description not passed in params')
	
	
	
	
	#==== create the deal entity ====#
	if origin == 'phone_merchant':
		logging.info('Origin from phone_merchant')
		user = params['user']
		
		if user.tester:
			deal_status = 'test'
		else:
			deal_status = 'active'
		
		
		
		deal = Deal(
				parent = user,
				is_exclusive = True,
				deal_status = deal_status,
				origin = 'merchant',
				pin_color = 'green',
				)
		
	elif origin	=='phone_existing_business' or origin == 'phone_new_business':
		#phone deals are the child of a ninja
		logging.debug('STOP!')
		uid = params['uid']
		
		# If it is one of the founders uploading a deal, then it should be uploaded by a rando ninja
		admin_users = ['Carl D.','Patch W.','Alonso H.','Ethan S.','Patrick W.','Pat W.']
		owner = Customer.get(uid)
		if owner.display_name in admin_users:
			undead_ninjas = Customer.all(keys_only=True).filter('email',UNDEAD_NINJA_EMAIL).fetch(None)
			uid = random.choice(undead_ninjas)
		
		deal = Deal(
						parent			= uid,
						is_exclusive	= False
						)
		
		if 'shareURL' in params:
			shareURL = params['shareURL']
			if shareURL:
				#shareURL was passed and is not empty
				logging.debug("shareURL: "+str(shareURL))
				share_id = shareURL.split('/')[-1] #grab share id
				logging.debug("share_id: "+str(share_id))
				deal.share_id = share_id
		
		
		
		development = params.get('development',False)
		if development:
			deal.deal_status = 'test'
		
		deal.date_end = datetime.now() + timedelta(days=7)
	
	#==== Link deal to blobstore image ====#
	if upload_flag == True:
		#an image has been uploaded, and the blob needs to be tied to the deal
		logging.debug('image uploaded')
		#if an image has been uploaded, add it to the deal. otherwise do nothing.
		#assumes that if an image already exists, that it the old one has been deleted elsewhere
		blob_key = params['img_key']
		deal.img= blob_key
	else:
		#an image was not uploaded. do nothing
		logging.debug('image not uploaded')
	
	
	
	
	
	
	#add the data
	try:
		deal.business = business
	except:
		log_error()
	deal.deal_text 			= deal_text
	deal.deal_type			= deal_type
	deal.description 		= description
	deal.tags				= list(set(tags)) #list->set->list removes duplicates
	deal.business_name		= business_name
	deal.businessID			= str(businessID)
	deal.vicinity			= vicinity
	deal.geo_point			= geo_point
	deal.geo_hash			= geo_hash
	
	#secondary_name
	if deal_type == 'bundle':
		deal.secondary_name = secondary_name
	
	
	
	#put the deal
	deal.put()
	
	remove_memcache_key_by_deal(deal)
	
	
	#dealput is the deal key i.e. dealID
	logging.debug(log_model_props(deal))
	logging.debug(log_model_props(business))
	
#	share_url = create_share_url(deal)

	
	if origin == 'phone_existing_business' or origin =='phone_new_business':
		#needs share url and dealID
		return deal
	else:
		#return share url
		return deal

#===============================================================================
# TODO: fit these into our system - needs to handle failure
#===============================================================================
#def prefetch_refprop(entities, prop):
#	ref_keys = [prop.get_value_for_datastore(x) for x in entities]
#	ref_entities = dict((x.key(), x) for x in db.get([i for i in set(ref_keys) if i]))
#	for entity, ref_key in zip(entities, ref_keys):
#		if ref_key:
#			prop.__set__(entity, ref_entities[ref_key])
#	return entities
#def prefetch_refprops(entities, *props):
#	'''
#	Prefetches reference properties. Credit to Nick Johnson
#	@param entities: a list of entities that reference other entities
#	@type entities: list of entities
#	@param *props: a list of reference property names in the entities
#	@type *param: list of strings
#	@return: the list of entities 
#	'''
#	fields = [(entity, prop) for entity in entities for prop in props]
#	ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
#	ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
#	for (entity, prop), ref_key in zip(fields, ref_keys):
#		prop.__set__(entity, ref_entities[ref_key])
#	return entities
#def prefetch_parents(entities):
#	'''
#	Prefetches parent entities. Credit to Bryce Cutt
#	Assigns parents 
#	@param entities: a list of entities with parents
#	@type entities: list
#	@return: a list of 
#	'''
#	ref_keys = [x.parent_key() for x in entities if x.parent_key() is not None]
#	ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
#	ref_entities[None] = None
#	for entity in entities:
#		entity.parent_obj = ref_entities[entity.parent_key()]
#	return entities















#===============================================================================
# Custom Properties
#===============================================================================
class GeoHashProperty(db.StringProperty):
	'''
	A property that automatically stores the geohash prefixes of an entity
	@requires: the entity must have a db.GeoPtProperty
	'''
	data_type = list
	def get_value_for_datastore(self, model_instance):
		'''
		Persist a list of geo_hash prefixes for the instance
		@param model_instance:
		@type model_instance:
		'''
		logging.debug('geo hash property')
		geo_point = getattr(model_instance, 'geo_point')
		precision = 8
		geo_hash = geohash.encode(geo_point.lat, geo_point.lon, precision)
		
		return geo_hash
class KeywordListProperty(db.StringListProperty):
	'''
	A property that creates a list of tags from the entity properties
	'''
	data_type = list
	def get_value_for_datastore(self, model_instance):
		'''
		@attention:  entities may have additional tags that were added by a business
		'''
#		tags = model_instance.extra_tags
		try:
			tags = model_instance.extra_tags
		except:
			tags = []
		tags.extend(model_instance.create_tags())
		return list(set(tags))
		


###################################################
###					CLASSES						###
###################################################


UNDEAD_NINJA_EMAIL = 'undeadninja@levr.com'
CUSTOMER_MODEL_VERSION = 1
class Customer(db.Model):
#root class
	
	#levr 
	levr_token		= db.StringProperty(required=True)#default=create_levr_token())
	email 			= db.EmailProperty()
	pw 				= db.StringProperty()
	alias			= db.StringProperty(default='')
	first_name		= db.StringProperty(default='')
	last_name		= db.StringProperty(default='')
	display_name	= db.StringProperty()
	photo			= db.StringProperty(default='http://www.levr.com/img/levr.png')
	
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=CUSTOMER_MODEL_VERSION)
	#user meta
	tester			= db.BooleanProperty(default=False)
	level			= db.IntegerProperty(default=0)
	karma			= db.IntegerProperty(default=1)
	new_notifications = db.IntegerProperty(default=0)
	
	# db references
	followers			= db.ListProperty(db.Key) # Customer
	favorites			= db.ListProperty(db.Key,default=[]) # Deal
	upvotes				= db.ListProperty(db.Key,default=[]) # Deal
	downvotes			= db.ListProperty(db.Key,default=[]) # Deal
	been_radius_blasted	= db.ListProperty(db.Key) # Deal
	
	#facebook
	facebook_connected	= db.BooleanProperty(default=False)
	facebook_token		= db.StringProperty() #not permanent
	facebook_id			= db.IntegerProperty()
	facebook_friends	= db.ListProperty(int)
	
	#foursquare
	foursquare_connected= db.BooleanProperty(default=False)
	foursquare_id		= db.IntegerProperty()
	foursquare_token	= db.StringProperty()
	foursquare_friends	= db.ListProperty(int)
	
	#twitter
	twitter_connected		= db.BooleanProperty(default=False)
	twitter_token			= db.StringProperty()
	twitter_token_secret	= db.StringProperty()
	twitter_id				= db.IntegerProperty()
	twitter_screen_name		= db.StringProperty()
	twitter_friends_by_id	= db.ListProperty(int)
	twitter_friends_by_sn	= db.ListProperty(str)
	
	#list of friends emails so we can find them when they log in
	email_friends		= db.ListProperty(str)
	
	#date stuff
	date_created		= db.DateTimeProperty(auto_now_add=True)
	date_last_edited	= db.DateTimeProperty(auto_now=True)
	date_last_login 	= db.DateTimeProperty(auto_now_add=True)
	date_last_notified 	= db.DateTimeProperty(auto_now_add=True)
	last_notified		= db.IntegerProperty(default=0)
	
	#only for businesses
	owner_of		= db.StringProperty()
	activation_code	= db.StringProperty()
	verified_owner	= db.BooleanProperty(default=False)
	
	#deprecated stuff
	group			= db.StringProperty(choices=set(["paid","unpaid"]),default="unpaid")
	payment_email	= db.EmailProperty()
	money_earned	= db.FloatProperty(default = 0.0) #new earning for all deals
	money_available = db.FloatProperty(default = 0.0) #aka payment pending
	money_paid		= db.FloatProperty(default = 0.0) #amount we have transfered
	redemptions		= db.StringListProperty(default = [])	#id's of all of their redeemed deals
	new_redeem_count= db.IntegerProperty(default = 0) #number of unseen redemptions
	vicinity		= db.StringProperty() #the area of the user, probably a college campus
	
	@property
	def following(self):
		#returns a query object that will return all followers of this user entity
		return Customer.all().filter('followers',self.key())
	
	def get_notifications(self,date=None):
		#returns a query object for all notifications since the specified date
		#reset user date_last_notified
		logging.debug('Customer.get_notifications')
		if date == None:
			#date was not specified, use the default
			date = self.last_notified
#			date = 0
		logging.debug('date: '+str(date))
		
		
		notifications = Notification.all().filter('to_be_notified',self.key()).filter('date_in_seconds >=',date).fetch(None)
		
#		#DEBUG
#		logging.debug('start debug')
#		dates = Notification.all(projection=['date_in_seconds']).filter('date_in_seconds <=',date).fetch(None)
#		logging.debug(dates)
#		for date in dates:
#			logging.debug(date.date_in_seconds)
#		logging.debug('end debug')
#		#/DEBUG
		
		now = datetime.now()
		logging.debug('now'+str(long(unix_time(now))))
		#reset last notification time
		self.last_notified = long(unix_time(now))
		self.date_last_notified = now
		#reset new_notifications counter
		self.new_notifications = 0
		
		#return all notifications
		return notifications
	
	


BUSINESS_MODEL_VERSION = 2
class Business(db.Model):
	'''
	Changelog:
	v2: added geo_hash_prefixes
	'''
	#root class
	business_name 	= db.StringProperty()
	vicinity		= db.StringProperty()
	geo_point		= db.GeoPtProperty() #latitude the longitude
	geo_hash		= GeoHashProperty()#db.StringProperty()
	
	types			= db.ListProperty(str)
	# TODO: add business tags
	tags			= KeywordListProperty()
	extra_tags		= db.StringListProperty()
	owner			= db.ReferenceProperty(Customer,collection_name='businesses')
	upload_email	= db.EmailProperty()
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	foursquare_id	= db.StringProperty()
	foursquare_name	= db.StringProperty()
	foursquare_linked	= db.BooleanProperty(default=False)
	phone			= db.StringProperty()
	activation_code = db.StringProperty()
	# TODO: give a business karma when a deal at the business gets upvotes - will factor into deal rank
	karma			= db.IntegerProperty(default=0)
	
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=BUSINESS_MODEL_VERSION)
	
	# deprecated
	targeted		= db.BooleanProperty()
	locu_id			= db.StringProperty()
	widget_id		= db.StringProperty(default=create_unique_id())
	creation_date	= db.DateTimeProperty(auto_now_add=True)
	
	def create_tags(self,stemmed=True):
		'''
		Used to parse the business fields into indexed keywords
		@return: a list of tokenized and stemmed keywords
		@rtype: list
		'''
		indexed_properties = ['business_name','types','foursquare_name']
		items = [getattr(self, prop) for prop in indexed_properties]
		text = ''
		logging.info('\n\n create business tags: '+repr(items)+' \n\n')
		for item in items:
#			logging.info(item)
			if item:
				if type(item) == list:
					text +=' '.join(item) + ' '
				else:
					try:
						text += item + ' '
					except:
						log_error('On busines: '+repr(self.business_name))
#			logging.info(text)
		logging.info('text: '+repr(text))
		tags = create_tokens(text,stemmed)
		logging.info('tags: '+str(tags))
		return tags
	

MERCHANT_DEAL_LENGTH = 21 # days
DEAL_STATUS_ACTIVE = 'active'
DEAL_STATUS_TEST = 'test'
DEAL_STATUS_REJECTED = 'rejected'
DEAL_STATUS_EXPIRED = 'expired'
DEAL_STATUS_PENDING = 'pending'
DEAL_MODEL_VERSION = 4
class Deal(polymodel.PolyModel):
	'''
	Changelog:
	v3: added promotions property - for identifying what promotions the deal is affected by
	v4: added geo_hash_prefixes
	'''
#Child of business owner OR customer ninja
	#deal meta information
	deal_status		= db.StringProperty(choices=set(["pending","active","rejected","expired","test"]),default="active")
	been_reviewed	= db.BooleanProperty(default=False)
	reject_message	= db.StringProperty()
	tags			= KeywordListProperty()#db.ListProperty(str)
	extra_tags		= db.StringListProperty()
	businessID 		= db.StringProperty()
	business		= db.ReferenceProperty(Business,collection_name='deals')
	origin			= db.StringProperty(default='levr')
	external_url	= db.StringProperty()
	foursquare_id	= db.StringProperty()
	foursquare_type	= db.StringProperty()
	
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=DEAL_MODEL_VERSION)
	
	#deal display info
	deal_text		= db.StringProperty(default='')
	geo_point		= db.GeoPtProperty() #latitude the longitude
	geo_hash		= GeoHashProperty()#db.StringProperty()
	description 	= db.StringProperty(multiline=True,default='') #description of deal
	img				= blobstore.BlobReferenceProperty()
	share_id		= db.StringProperty(default=create_unique_id())
	#pin_color		= db.StringProperty(choices=set(['red','blue','green','pink','orange']),default='red')
	pin_color		= db.StringProperty(default='red')
	rank			= db.IntegerProperty(default = 0)
	
	
	#deal interactions
	upvotes			= db.IntegerProperty(default=0)
	downvotes		= db.IntegerProperty(default=0)
	karma			= db.IntegerProperty(default=0)
	promotions		= db.ListProperty(str)
	
	
	#date stuff
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	date_end 		= db.DateTimeProperty(auto_now_add=False)
	
	
	#deprecated stuff
	date_uploaded	= db.DateTimeProperty()
	date_start 		= db.DateTimeProperty() #start date
	has_been_shared	= db.BooleanProperty()
	count_seen 		= db.IntegerProperty()  #number seen
	deal_views		= db.IntegerProperty()
	barcode			= blobstore.BlobReferenceProperty()
	secondary_name 	= db.StringProperty() #== with purchase of
	deal_type 		= db.StringProperty() #two items or one item
	count_redeemed 	= db.IntegerProperty() 	#total redemptions
	vicinity		= db.StringProperty()
	business_name 	= db.StringProperty() #name of business
	is_exclusive	= db.BooleanProperty()
	locu_id			= db.StringProperty()
	
	def create_tags(self,business=None,stemmed=True,filtered=True):
		'''
		Creates a list of keywords from the indexed properties of the deal
		
		@param business: the business of the deal
		@type business: Business
		@param stemmed: Optional, if true, then will also stem the keywords
		@type stemmed: bool
		'''
		
		indexed_properties = ['deal_text','description']
		
		# create tags from the deal properties
		items = [getattr(self, prop) for prop in indexed_properties]
		text = ''
		for item in items:
#			logging.info(item)
			if item:
				if type(item) == list:
					text +=' '.join(item) + ' '
				else:
					try:
						text += item + ' '
					except:
						log_error('On deal: '+repr(self.key()))
#			logging.info(text)
		logging.info('text: '+repr(text))
		
		# create the tags from the compiled string
		tags = create_tokens(text,stemmed,filtered)
		
		logging.info('tags: '+str(tags))
		
		#=======================================================================
		# Create tags from the business
		#=======================================================================
		# will pull the business from the db by default
		if not business:
			business = self.business
		# create tags from the business
		tags.extend(business.create_tags())
		
		tags = list(set(tags))
		logging.info('total_tags: '+repr(tags))
		# return list of tags without redundancies
		return tags
	
	def expire(self,notify=False):
		'''
		Sets the deal_status to expired and performs any other actions necessary
			to expire the deal properly
		Removes the deals memcache entry
		Sets the deals expiration date to right now
		
		@attention: Does not put deal before returning.
		
		@param notify: Determines whether or not the owner will be notified
		@type notify: bool
		
		@return: self
		@rtype: Deal
		
		'''
		# reset the memcache entry
		remove_memcache_key_by_deal(self)
		
		# set deal status to expired
		self.deal_status = DEAL_STATUS_EXPIRED
		
		# set the expiration date to right now
		self.date_end = datetime.now()
		
		if notify:
			pass
			# notifies the owner that their deal has been expired
			# TODO: notify the deals owner that their deal has expired
			
			#grab the deal owner
	#		to_be_notified = deal.key().parent()
	#		#create the notification
	#		levr.create_notification('expired',to_be_notified,None,deal.key())
		return self
	def reanimate(self,date_end=None):
		'''
		Reactivates a deal. Performs auxiliary actions beyond setting
			deal status to active
		
		@attention: Does not put deal before returning
		
		@param date_end: The date to expire the deal. None if deal doesnt expire
		@type date_end: datetime.datetime
		
		@return: self
		'''
		# Eliminate the memcache entry
		
		# Determine whether or not the deal status should be set to active or test
		owner = self.parent()
		if owner.tester:
			self.deal_status = DEAL_STATUS_TEST
		else:
			self.deal_status = DEAL_STATUS_ACTIVE
		
		remove_memcache_key_by_deal(self)
		
		# reset the end date
		self.date_end = date_end
		
		return self
	@property
	def views(self):
		'''
		Retrieve the number of views for this deal
		
		@return: total
		@rtype: int
		'''
		total = 0
		for counter in DealViewCounter.all().ancestor(self):
			total += counter.count
		
		return total
	
	@db.transactional
	def increment_views(self):
		'''
		Increments the number of times this deal has been viewed
		'''
		index = random.randint(0,NUM_DEAL_VIEW_COUNTERS-1)
		shard_name = str(self.key())+'|shard'+str(index)
		counter = DealViewCounter.get_by_key_name(shard_name,self)
		if counter is None:
			counter = DealViewCounter(key_name=shard_name,parent=self)
		counter.count += 1
		counter.put()
		return
	
NUM_DEAL_VIEW_COUNTERS = 10
class DealViewCounter(db.Model):
	'''
	Sharded deal view counters
	
	Must be a child of a deal
	'''
	count = db.IntegerProperty(required=True,default=0)

PROMOTION_MODEL_VERSION = 1
class DealPromotion(db.Model):
	'''
	A record for a promotion that has been bought
	Changelog:
	v1:
	
	'''
	purchaser = db.ReferenceProperty(Customer,required=True,collection_name='purchased_promotions_history')
	deal = db.ReferenceProperty(Deal,required=True,collection_name='purchased_promotions_history')
	date = db.DateTimeProperty(auto_now_add=True)
	promotion_id = db.StringProperty(required=True,choices=set([
													promo.BOOST_RANK,
													promo.MORE_TAGS,
													promo.NOTIFY_PREVIOUS_LIKES,
													promo.NOTIFY_RELATED_LIKES,
													promo.RADIUS_ALERT
													])
									)
	receipt = db.StringProperty()
	tags = db.StringListProperty()
	model_version = db.IntegerProperty(default=PROMOTION_MODEL_VERSION)


NOTIFICATION_MODEL_VERSION = 1
class Notification(db.Model):
	# Only has outbound references, no inbound
	date				= db.DateTimeProperty(auto_now_add=True)
	date_in_seconds		= db.IntegerProperty()
	notification_type	= db.StringProperty(choices=set(['favorite','followedUpload','newFollower','levelup','shared','levr','expired']))
	to_be_notified		= db.ListProperty(db.Key)
	line2				= db.StringProperty(default='')
	actor				= db.ReferenceProperty(Customer)
	deal				= db.ReferenceProperty(Deal,collection_name='notifications')
	#metadata used for migrations
	model_version		= db.IntegerProperty(default=NOTIFICATION_MODEL_VERSION)
	
	def _add_basics(self):
		self.date_in_seconds = long(unix_time(datetime.now()))
		return
	def _return(self,to_be_returned):
		'''
		A wrapper for returning to valididate the notification creation process
		Because of the way the notification creation functions are called,
			properties cannot be required. This serves that function instead.
		
		@param to_be_returned: Whatever you want to return
		@type to_be_returned: Whatever.
		'''
		assert self.date_in_seconds, 'Did not set date_in_seconds'
		assert self.notification_type, 'Did not set notification_type'
		assert self.to_be_notified, 'Did not set to_be_notified'
		assert self.line2, 'Did not set line2'
		assert self.actor, 'Did not set actor'
		
		return to_be_returned
		
	def create_radius_alert(self,to_be_notified,deal):
		'''
		Creates a notification when someone searches within a radius of the deal
		@param to_be_notified: a single customer, because only one person searches at a time
		@type to_be_notified: Customer
		@param deal: deal entity
		@type deal: Deal
		
		@return: the user that is being notified
		@rtype: Customer
		'''
		to_be_notified.new_notifications += 1
		to_be_notified.been_radius_blasted.append(deal.key())
		to_be_notified.put()
		
		self.notification_type = 'followedUpload'
		self.line2 = 'wants to share a deal with you.'
		self.to_be_notified = [to_be_notified.key()]
		self.deal = deal
		self.actor = deal.parent_key()
		# add uni
		self._add_basics()
		self.put()
		
		return self._return(to_be_notified)

REPORTED_DEAL_MODEL_VERSION = 1
class ReportedDeal(db.Model):
	# Only has outbound references, no inbound
	uid				= db.ReferenceProperty(Customer,collection_name='reported_deals')
	deal			= db.ReferenceProperty(Deal,collection_name='reported_deals')
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=REPORTED_DEAL_MODEL_VERSION)

BUSINESS_BETA_REQUEST_MODEL_VERSION = 2
class BusinessBetaRequest(db.Model):
	business_name	= db.StringProperty()
	business_type	= db.StringProperty()
	city			= db.StringProperty()
	owner_name		= db.StringProperty()
	owner_email		= db.StringProperty()
	use_case		= db.StringProperty()
	date_created	= db.DateTimeProperty(auto_now_add=True)
	
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=BUSINESS_BETA_REQUEST_MODEL_VERSION)
	
	#deprecated
	contact_name	= db.StringProperty()
	contact_email	= db.StringProperty()
	contact_phone	= db.StringProperty()
	
FLOATING_CONTENT_MODEL_VERSION = 1
class FloatingContent(db.Model):
	#only has outbound references, no inbound
	action				= db.StringProperty(required=True,choices=set(['upload','deal']))
	contentID			= db.StringProperty(required=True)
	origin				= db.StringProperty()
	user				= db.ReferenceProperty(Customer,collection_name='floating_content')
	deal				= db.ReferenceProperty(Deal,collection_name='floating_content')
	business			= db.ReferenceProperty(Business,collection_name='floating_content')
	#metadata used for migrations
	model_version		= db.IntegerProperty(default=FLOATING_CONTENT_MODEL_VERSION)


class UndeadNinjaBlobImgInfo(db.Model):
	img = blobstore.BlobReferenceProperty()
	gender = db.StringProperty(choices=set(['male','female','either']))
	ninja = db.Reference(Customer, collection_name='img_ref')
