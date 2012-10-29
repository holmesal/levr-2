from common_word_list import blacklist
from datetime import datetime, timedelta
from google.appengine.api import taskqueue, memcache
from google.appengine.ext import blobstore, db
from google.appengine.ext.db import polymodel
import base_62_converter as converter
import geo.geohash as geohash
import json
import levr_encrypt as enc
import logging
import os
import random
import re
import sys
import traceback
import uuid
from math import floor, sqrt
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
def create_new_business(business_name,vicinity,geo_point,types,**kwargs):
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
	assert type(geo_point) == db.GeoPt, 'Must pass geo_point as a db.GeoPt property'
	assert type(types) == list, 'Must pass types as a list'
	
	
	business = Business(
					business_name = business_name,
					vicinity = vicinity,
					geo_point = geo_point,
					types = types
					)
	
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
			#user is the person being notified
			users = db.get(to_be_notified)
			
			#set the phrase
			line2 = 'Has uploaded a new offer.'
			
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
	try:
		lat, lng = geo_str.split(',')
		return db.GeoPt(lat=float(lat), lon=float(lng))
	except Exception,e:
		log_error(e)
		raise TypeError('lat,lon: '+str(geo_str))

def tagger(text): 
	# text is a string
#	parsing function for creating tags from description, etc
	#replace commas with spaces
	text = text.replace(","," ")
	#replace underscores with spaces
	text = text.replace("_"," ")
	text = text.replace("/"," ")
	#remove all non text characters
	text = re.sub(r"[^\w\s]", '', text)
	#parse text string into a list of words if it is longer than 2 chars long
	tags = [w.lower() for w in re.findall("[\'\w]+", text)]# if len(w)>2]
	#remove redundancies
	tags = list(set(tags))
	#remove unwanted tags
	filtered_tags = []
	for tag in tags:
		if tag.isdigit() == False:
			#tag is not a number 
			if tag not in blacklist:
				filtered_tags.append(tag)
	
	return filtered_tags

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
		logging.warning('There was an error in log_model_props %s',e)
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
		logging.warning('There was an error in log_dir')
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
		logging.warning('There was an error in log_dict %s',e)
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
	taskqueue.add(url='/tasks/newUserTextTask',payload=json.dumps(task_params))


MEMCACHE_ACTIVE_GEOHASH_NAMESPACE = 'active_geohash'
MEMCACHE_TEST_GEOHASH_NAMESPACE = 'test_geohash'
def update_deal_key_memcache(geo_point,dealID,namespace):
	'''
	Updates the geohash+deal_key memcache when one of the geohashes has been updated and the memcache now has stale information
	Typical use case: a new deal was uploaded and the memcache key (i.e. the new deals geohash) needs to be updated
	or deleted.
	@param geo_point: the geopoint of the deal
	@type geo_point: db.GeoPt
	@param dealID: the deals unencrypted key
	@type dealID: db.Key
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
#	
	# This is for actually updating the memcache. 
	# Grab the existing hashes from the memcache
	
#	
##	while True and failsafe <50:
#	for i in range(0,5): #@UnusedVariable
#		failsafe += 1
#		logging.debug(failsafe)
#		#grab existing mappings
#		existing_mappings = client.get_multi(geo_hash_list, '', namespace, True)
#		logging.info(existing_mappings)
##		unresolved_keys = filter(lambda x: x not in existing_mappings,geo_hash_list)
#		
#		#update the mappings that exist in the memcache
#		for key in existing_mappings:
#			existing_mappings[key].append(dealID)
#		unresolved_keys = client.cas_multi(existing_mappings, 0, '',0, namespace)
#		logging.info('unresolved_keys: '+repr(unresolved_keys))
#		if not unresolved_keys:
#			# Everything was updated properly
#			break
#		else:
#			# Some keys were not updated. Update list of geo_hashes for next loop
#			geo_hash_list = unresolved_keys
#			logging.info('cas_multi failed on keys: {}'.format(unresolved_keys))
#			break
#	logging.info(failsafe)

	#============================================================================
	# while True: # Retry loop
	#  counter = client.gets(key)
	#  assert counter is not None, 'Uninitialized counter'
	#  if client.cas(key, counter+1):
	#     break
	#============================================================================


def dealCreate(params,origin,upload_flag=True):
	'''pass in "self"'''
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
#		business= Business.gql("WHERE business_name=:1 and geo_point=:2", business_name, geo_point).get()
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
		deal_text	= params['deal_line1']
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
			'deal is NOT bundled'
			deal_type = 'single'
	else:
		#phone uploaded deals do not pass deal_line2
		deal_type = 'single'
	
	#description
	if 'deal_description' in params:
		description = params['deal_description']
		#truncate description to a length of 500 chars
		description = description[:500]
		tags.extend(tagger(description))
	else:
		raise KeyError('deal_description not passed in params')
	
	
	
	
	#==== create the deal entity ====#
	if origin	== 'merchant_create':
		#web deals get active status and are the child of the owner
		ownerID = params['uid']
		ownerID = enc.decrypt_key(ownerID)
		
		deal = Deal(parent = db.Key(ownerID))
		deal.is_exclusive		= True

	elif origin	=='merchant_edit':
		dealID	= params['deal']
		dealID	= enc.decrypt_key(dealID)
		deal	= Deal.get(dealID)

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

	elif origin == 'admin_review':
		#deal has already been uploaded by ninja - rewriting info that has been reviewed
		dealID = enc.decrypt_key(params['deal'])
		deal = Deal.get(db.Key(dealID))
		deal.been_reviewed		= True
		deal.date_start			= datetime.now()
		days_active				= int(params['days_active'])
		deal.date_end			= datetime.now() + timedelta(days=days_active)
		
		new_tags = params['extra_tags']
		tags.extend(tagger(new_tags))
		logging.debug('!!!!!!!!!!!!')
		logging.debug(tags)
	
	
	#==== Link deal to blobstore image ====#
	if upload_flag == True:
		#an image has been uploaded, and the blob needs to be tied to the deal
		logging.debug('image uploaded')
		if origin == 'merchant_edit' or origin == 'admin_review':
			#an image was uploaded, so remove the old one.
			blob = deal.img
			blob.delete()
		#if an image has been uploaded, add it to the deal. otherwise do nothing.
		#assumes that if an image already exists, that it the old one has been deleted elsewhere
		blob_key = params['img_key']
		deal.img= blob_key
	else:
		#an image was not uploaded. do nothing
		logging.debug('image not uploaded')
	
	
	
	
	
	
	#add the data
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
	
	if deal.deal_status == 'active':
		namespace = MEMCACHE_ACTIVE_GEOHASH_NAMESPACE
	elif deal.deal_status == 'test':
		namespace = MEMCACHE_TEST_GEOHASH_NAMESPACE
	else:
		raise Exception('Invalid memcache namespace')
	logging.debug('Updating memcache')
	logging.info('updating memcahce')
	update_deal_key_memcache(deal.geo_point,deal.key(),namespace)
	
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






















###################################################
###					CLASSES						###
###################################################


UNDEAD_NINJA_EMAIL = 'undeadninja@levr.com'
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
	model_version	= db.IntegerProperty(default=1)
	#user meta
	tester			= db.BooleanProperty(default=False)
	level			= db.IntegerProperty(default=0)
	karma			= db.IntegerProperty(default=1)
	new_notifications = db.IntegerProperty(default=0)
	
	# db references
	followers		= db.ListProperty(db.Key) # Customer
	favorites		= db.ListProperty(db.Key,default=[]) # Deal
	upvotes			= db.ListProperty(db.Key,default=[]) # Deal
	downvotes		= db.ListProperty(db.Key,default=[]) # Deal
	
	
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
	
#===============================================================================
	#===========================================================================
	# Do not use this. It is not complete
	#===========================================================================
#	def merge_into_user(self,new_user):
#		'''
#		Merges two accounts. new_user will cannibalize the user that this method is called on.
#		This includes transferring all of the old users information.
#		
#		@param new_user:
#		@type new_user: Customer
#		'''
#		
#		new_user = self.secure_delete(self,new_user)
#		return new_user
#	
#	def secure_delete(self,new_user=None):
#		'''
#		Securely deletes a Customer entity by removing all references to the entity in the database
#		and then calling db.Models delete method on the entity. See ya.
#		
#		If new_user is passed, then instead of deleting all relational references, they are transfered to the new user
#		
#		@param new_user: 
#		@type new_user: Customer
#		'''
#		old_key = self.key()
#		new_key = new_user.key()
#		
#		#=======================================================================
#		# Notifications
#		# Delete the notifications
#		#=======================================================================
#		# to_be_notified notifications
#		to_be_notified = Notification.all().filter('to_be_notified',old_key).fetch(None)
#		# actor notifications
#		actor = self.notification_set.fetch(None)
#		
#		notes = set([])
#		notes.update(to_be_notified)
#		notes.update(actor)
#		
#		
#		logging.debug('Notifications: {}'.format(to_be_notified.__len__()+actor.__len__()))
#		
#		
#		if new_user:
#			#transfer notifications
#			#exchange to_be_notified
#			for note in notes:
#				#user exists in to_be_notified
#				if old_key in user.to_be_notified:
#					#remove old reference
#					note.to_be_notified.remove(old_key)
#					#add new reference
#					note.to_be_notified.append(new_key)
#				# otherwise, user is the actor
#				else:
#					note.actor = new_user
#			db.put(notes)
#		else:
#			#delete all notifications
#			notes = set([])
#			notes.update(to_be_notified)
#			notes.update(actor)
#			db.delete(notes)
#		
#		#=======================================================================
#		# Other Customers
#		# Remove reference links
#		#=======================================================================
#		users = Customer.all().filter('followers',old_key).fetch(None)
#		# remove the deleted users key
#		for user in users:
#			#remove old reference
#			user.followers.remove(old_key)
#			#add new reference if there is one
#			if new_user:	user.followers.append(new_key)
#			
#		logging.debug(users)
#		logging.debug('Follower references: {}'.format(users.__len__()))
#		db.put(users)
#		
#		#=======================================================================
#		# Deal
#		# 
#		#=======================================================================
#		deals = Deal.all().ancestor(old_key).fetch(None)
#		logging.debug('Child Deals: {}'.format(deals.__len__()))
#		
#		for deal in deals:
#			if new_user:
#				#transfer ownership
#				deal.transfer_ownership_to(new_user)
#			else:
#				#secure deletion
#				deal.secure_delete()
#		
#		
#		
#		#=======================================================================
#		# Business
#		# Empty the reference property
#		#=======================================================================
#		businesses = self.businesses.fetch(None)
#		for business in businesses:
#			#update or remove ownership
#			if new_user:	business.owner = new_user
#			else:			business.owner = None
#		logging.debug('Businesses ownership: {}'.format(businesses.__len__()))
#		db.put(businesses)
#		
#		
#		#=======================================================================
#		# ReportedDeal
#		# Remove reference link
#		#=======================================================================
#		reported_deals = self.reported_deals.fetch(None)
#		for deal in reported_deals:
#			# Transfer or remove ownership
#			if new_user:	deal.uid = new_user
#			else:			deal.uid = None
#		logging.debug('ReportedDeals: {}'.format(reported_deals.__len__()))
#		db.put(reported_deals)
#		
#		#=======================================================================
#		# FloatingContent
#		# Delete the content - it is now irrelevant
#		#=======================================================================
#		floating_content = self.floating_content.fetch(None)
#		logging.debug('Floating content removed: {}'.format(floating_content.__len__()))
#		
#		if new_user:
#			# Update reference
#			for content in floating_content:
#				content.user = new_user
#			db.put(floating_content)
#		else:
#			# Delete the content... no longer relevant
#			db.delete(floating_content)
#		
#		#call the users delete function to delete the user
# #		self.delete()
#		
#		return
#===============================================================================
	
	
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
	




#class BusinessOwner(db.Model):
#	email 			= db.EmailProperty()
#	pw 				= db.StringProperty()
#	validated		= db.BooleanProperty(default=False)
#	date_created	= db.DateTimeProperty(auto_now_add=True)
#	date_last_edited= db.DateTimeProperty(auto_now=True)
	
	#psudoproperty: businesses - see business entity - this is a query for all the businesses that list this owner as the owner

class Business(db.Model):
	#root class
	business_name 	= db.StringProperty()
	vicinity		= db.StringProperty()
	geo_point		= db.GeoPtProperty() #latitude the longitude
	geo_hash		= db.StringProperty()
	types			= db.ListProperty(str)
	
	owner			= db.ReferenceProperty(Customer,collection_name='businesses')
	upload_email	= db.EmailProperty()
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	foursquare_id	= db.StringProperty()
	foursquare_name	= db.StringProperty()
	foursquare_linked	= db.BooleanProperty(default=False)
	phone			= db.StringProperty()
	activation_code = db.StringProperty()
	# TODO: give a business karma when a deal at the business gets upvotes
	karma			= db.IntegerProperty(default=0)
	
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=1)
	
	# deprecated
	targeted		= db.BooleanProperty()
	locu_id			= db.StringProperty()
	widget_id		= db.StringProperty(default=create_unique_id())
	creation_date	= db.DateTimeProperty(auto_now_add=True)
	def create_tags(self):
		#create tags list
		tags = []
		
		#takes a business, and returns critical properties taggified
		business_name	= tagger(self.business_name)
		tags.extend(business_name)
#		vicinity		= tagger(self.vicinity)
#		tags.extend(vicinity)
#		
		for t in self.types:
			t			= tagger(t)
			tags.extend(t)
		
		return tags

class Deal(polymodel.PolyModel):
#Child of business owner OR customer ninja
	#deal meta information
	deal_status		= db.StringProperty(choices=set(["pending","active","rejected","expired","test"]),default="active")
	been_reviewed	= db.BooleanProperty(default=False)
	reject_message	= db.StringProperty()
	tags			= db.ListProperty(str)
	businessID 		= db.StringProperty() #CHANGE TO REFERENCEPROPERTY
	business		= db.ReferenceProperty(Business)
	origin			= db.StringProperty(default='levr')
	external_url	= db.StringProperty()
	foursquare_id	= db.StringProperty()
	foursquare_type	= db.StringProperty()
	
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=1)
	
	#deal display info
	deal_text		= db.StringProperty(default='')
	geo_point		= db.GeoPtProperty() #latitude the longitude
	geo_hash		= db.StringProperty()
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
	
	#for the merchants
	deal_views		= db.IntegerProperty(default=0)
	
	#date stuff
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	date_end 		= db.DateTimeProperty(auto_now_add=False)
	
	#may be deprecated.. in limbo
	date_uploaded	= db.DateTimeProperty(auto_now_add=True)
	date_start 		= db.DateTimeProperty(auto_now_add=False) #start date
	has_been_shared	= db.BooleanProperty(default = False)
	count_seen 		= db.IntegerProperty(default = 0)  #number seen
	
	#deprecated stuff
	barcode			= blobstore.BlobReferenceProperty()
	secondary_name 	= db.StringProperty(default='') #== with purchase of
	deal_type 		= db.StringProperty(choices=set(["single","bundle"])) #two items or one item
	count_redeemed 	= db.IntegerProperty() 	#total redemptions
	vicinity		= db.StringProperty()
	business_name 	= db.StringProperty() #name of business
	is_exclusive	= db.BooleanProperty(default=False)
	locu_id			= db.StringProperty()
	
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
		# TODO: add shards to memcache?
		index = random.randint(0,NUM_DEAL_VIEW_COUNTERS-1)
		shard_name = 'shard'+str(index)
		counter = DealViewCounter.get_by_key_name(shard_name,self)
		if counter is None:
			counter = DealViewCounter(key_name=shard_name,parent=self)
		counter.count += 1
		counter.put()
		
NUM_DEAL_VIEW_COUNTERS = 10
class DealViewCounter(db.Model):
	'''
	Sharded deal view counters
	
	Must be a child of a deal
	'''
	count = db.IntegerProperty(required=True,default=0)

class Notification(db.Model):
	# Only has outbound references, no inbound
	date				= db.DateTimeProperty(auto_now_add=True)
	date_in_seconds		= db.IntegerProperty()
	notification_type	= db.StringProperty(required=True,choices=set(['favorite','followedUpload','newFollower','levelup','shared','levr','expired']))
	line2				= db.StringProperty(default='')
	to_be_notified		= db.ListProperty(db.Key)
	deal				= db.ReferenceProperty(Deal,collection_name='notifications')
	actor				= db.ReferenceProperty(Customer)
	#metadata used for migrations
	model_version		= db.IntegerProperty(default=1)



class ReportedDeal(db.Model):
	# Only has outbound references, no inbound
	uid				= db.ReferenceProperty(Customer,collection_name='reported_deals')
	deal			= db.ReferenceProperty(Deal,collection_name='reported_deals')
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=1)
	
class BusinessBetaRequest(db.Model):
	business_name	= db.StringProperty()
	contact_name	= db.StringProperty()
	contact_email	= db.StringProperty()
	contact_phone	= db.StringProperty()
	date_created	= db.DateTimeProperty(auto_now_add=True)
	#metadata used for migrations
	model_version	= db.IntegerProperty(default=1)
	
class FloatingContent(db.Model):
	#only has outbound references, no inbound
	action				= db.StringProperty(required=True,choices=set(['upload','deal']))
	contentID			= db.StringProperty(required=True)
	origin				= db.StringProperty()
	user				= db.ReferenceProperty(Customer,collection_name='floating_content')
	deal				= db.ReferenceProperty(Deal,collection_name='floating_content')
	business			= db.ReferenceProperty(Business,collection_name='floating_content')
	#metadata used for migrations
	model_version		= db.IntegerProperty(default=1)


class UndeadNinjaBlobImgInfo(db.Model):
	img = blobstore.BlobReferenceProperty()
	gender = db.StringProperty(choices=set(['male','female','either']))
	ninja = db.Reference(Customer, collection_name='img_ref')
