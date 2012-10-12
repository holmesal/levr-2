from common_word_list import blacklist
from datetime import datetime, timedelta
from google.appengine.api import taskqueue
from google.appengine.ext import blobstore, db
from google.appengine.ext.db import polymodel
from random import randint, randint
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
def create_notification(notification_type,to_be_notified,actor,deal=None):
	'''
	notification_type	= choices: 
	'thanks',
	'favorite', 
	'followerUpload', 
	'newFollower', 
	'levelup'
	
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
	# If ths fundamentally changes, remember to change the undead ninja activity
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
			
			
			#add the actor to the list of followers
			# if actor not in user.followers:
#				user.followers.append(actor)
# 			else:
# 				#do nothing
# 				return True
			
			#set the phrase
			line2 = 'Has subscribed to your offers.'
			
			#increment the number of notifications
			user.new_notifications += 1
			
			#replace user
			db.put(user)
		elif notification_type == "followedUpload":
			#user is the person being notified
			user = Customer.get(to_be_notified[0])
			
			#set the phrase
			line2 = 'Has uploaded a new offer.'
			
			#increment the number of notifications
			user.new_notifications += 1
			
			#replace user
			db.put(user)
			
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
			
			#write line2
			line2 = 'You are now level 99. Woohoo!'
			
			#replace user
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
		log_error()
		return False
	else:
		return True


def geo_converter(geo_str):
	try:
		lat, lng = geo_str.split(',')
		return db.GeoPt(lat=float(lat), lon=float(lng))
	except Exception,e:
		raise TypeError('lat,lon: '+str(geo_str))

def tagger(text): 
	# text is a string
#	parsing function for creating tags from description, etc
	#replace commas with spaces
	text = text.replace(","," ")
	#replace underscores with spaces
	text = text.replace("_"," ")
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
	
	'''

	
	#####merchant_edit
		params = {
				'uid'			#uid is businessOwner
				'business'		#businessID
				'deal'			#dealID
				'deal_description'
				'deal_line1'
				'deal_line2'
				}
		!!! check for uploaded image !!!
		

	#####merchant_create
		params = {
				'uid'			#uid is businessOwner
				'business'
				'deal_line1'
				'deal_line2' 	#optional
				'deal_description'
				'img_key'
				}
		
	#####phone_existing_business
		params = {
				'uid' 			#uid is ninja
				'business' 
				'deal_description'
				'deal_line1'
				!!! no deal_line2 !!!
				}
	#####phone_new_business
		params = {
				'uid'			#uid is ninja
				'business_name'
				'geo_point'
				'vicinity'
				'types'
				'deal_description'
				'deal_line1'
				}
	#####admin_review
		params = {
				'uid'		#uid is ninja
				'deal'		#deal id
				'business'	#business id
				'deal_line1'
				'deal_line2'
				'deal_description'
				'tags'
				'end date'
				!!! other stuff !!!
				}
	'''
	
	
	#==== deal information ====#
	
	
	#==== business stuff ====#
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
			logging.debug('start types')
			logging.debug(types)
			logging.debug(type(types))
			types = tagger(types)
			logging.debug(types)
			logging.debug('end types')
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
			
			t = taskqueue.add(url='/tasks/businessHarmonizationTask',payload=json.dumps(task_params))
			
			
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
	#====Deal Information Lines ====#
	#deal line 1
	if 'deal_line1' in params:
		deal_text	= params['deal_line1']
		logging.debug(deal_text)
		tags.extend(tagger(deal_text))
		logging.info(tags)
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
		logging.debug(description.__len__())
		description = description[:500]
		logging.debug(description)
		tags.extend(tagger(description))
		logging.info(tags)
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
		
		
		deal = CustomerDeal(
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
		deal = CustomerDeal.get(db.Key(dealID))
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
	
	#user meta
	tester			= db.BooleanProperty(default=False)
	level			= db.IntegerProperty(default=1)
	karma			= db.IntegerProperty(default=0)
	new_notifications = db.IntegerProperty(default=0)
	
	#notifications, favorites, upvotes, etc...
	followers		= db.ListProperty(db.Key)
	favorites		= db.ListProperty(db.Key,default=[])
	upvotes			= db.ListProperty(db.Key,default=[])
	downvotes		= db.ListProperty(db.Key,default=[])
	
	
	#facebook
	facebook_connected	= db.BooleanProperty(default=False) #not required if have id
	facebook_token		= db.StringProperty() #not permanent
	facebook_id			= db.IntegerProperty()
	facebook_friends	= db.ListProperty(int)
	
	#foursquare
	foursquare_connected= db.BooleanProperty(default=False) #not required if have id
	foursquare_id		= db.IntegerProperty()
	foursquare_token	= db.StringProperty()
	foursquare_friends	= db.ListProperty(int)
	
	#twitter
	twitter_connected		= db.BooleanProperty(default=False) #not required if have id
	twitter_token			= db.StringProperty()
	twitter_token_secret	= db.StringProperty()
	twitter_id				= db.IntegerProperty()
	twitter_screen_name		= db.StringProperty()
	twitter_friends_by_id	= db.ListProperty(int)
	twitter_friends_by_sn	= db.ListProperty(str)
	
	#list of friends emails so we can find them when they log in
	email_friends		= db.ListProperty(str)
	
	#date stuff
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	date_last_login = db.DateTimeProperty(auto_now_add=True)
	date_last_notified = db.DateTimeProperty(auto_now_add=True)
	last_notified	= db.IntegerProperty(default=0)
	
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
	targeted		= db.BooleanProperty(default=False)
	owner			= db.ReferenceProperty(Customer,collection_name='businesses')
	upload_email	= db.EmailProperty()
	creation_date	= db.DateTimeProperty(auto_now_add=True)
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	widget_id		= db.StringProperty(default=create_unique_id())
	foursquare_id	= db.StringProperty()
	foursquare_name	= db.StringProperty()
	foursquare_linked	=	db.BooleanProperty(default=False)
	phone			= db.StringProperty()
	activation_code = db.StringProperty()
	locu_id			= db.StringProperty()
	karma			= db.IntegerProperty(default=0)


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
	origin			= db.StringProperty(default='levr')
	external_url	= db.StringProperty()
	locu_id			= db.StringProperty()
	foursquare_id	= db.StringProperty()
	foursquare_type	= db.StringProperty()
	
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
	count_redeemed 	= db.IntegerProperty(default = 0) 	#total redemptions
	vicinity		= db.StringProperty()
	business_name 	= db.StringProperty(default='') #name of business
	is_exclusive	= db.BooleanProperty(default=False)
	
	
	
	


class CustomerDeal(Deal):
#Sub-class of deal
#A deal that has been uploaded by a user

	gate_requirement= db.IntegerProperty(default = 5) #threshold of redeems that must be passed to earn a gate
	gate_payment_per= db.IntegerProperty(default = 1) #dollar amount per gate
	gate_count		= db.IntegerProperty(default = 0) #number of gates passed so far
	gate_max		= db.IntegerProperty(default = 5) #max number of gates allowed
	earned_total	= db.FloatProperty(default = 0.0) #amount earned by this deal
	paid_out		= db.FloatProperty(default = 0.0) #amount paid out by this deal
	
	def share_deal(self):
		if self.has_been_shared == False:
			#deal has never been shared before
			#flag that it has been shared
			self.has_been_shared = True
			
			#increase the max payment gates the ninja can earn
			self.gate_max += 5
		else:
			#deal has been shared - do nothing
			pass
		return self.has_been_shared
	
	def update_earned_total(self):
		#what was self.earned_total to start with?
		old = self.earned_total
		#update
		self.earned_total = float(self.gate_count*self.gate_payment_per)
		#if changed, find the difference
		difference = 0.0
		if self.earned_total > old:
			difference = self.earned_total - old
			logging.info('Earned ' + difference.__str__() + ' dollar!')
			
		return difference
	

class Notification(db.Model):
	date			= db.DateTimeProperty(auto_now_add=True)
	date_in_seconds	= db.IntegerProperty()
	notification_type = db.StringProperty(required=True,choices=set(['redemption','thanks','favorite','followedUpload','newFollower','levelup']))
	line2			= db.StringProperty(default='')
#	owner			= db.ReferenceProperty(Customer,collection_name='notifications',required=True)
	to_be_notified	= db.ListProperty(db.Key)
	deal			= db.ReferenceProperty(Deal,collection_name='notifications')
	actor			= db.ReferenceProperty(Customer)
	

class CashOutRequest(db.Model):
#child of ninja
	amount			= db.FloatProperty()
	date_paid		= db.DateTimeProperty()
	status			= db.StringProperty(choices=set(['pending','paid','rejected']))
	payKey			= db.StringProperty()
	money_available_paytime	= db.FloatProperty()
	note			= db.StringProperty()
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)

class ReportedDeal(db.Model):
	uid				= db.ReferenceProperty(Customer,collection_name='reported_deals')
	dealID			= db.ReferenceProperty(Deal,collection_name='reported_deals')
	date_created	= db.DateTimeProperty(auto_now_add=True)
	date_last_edited= db.DateTimeProperty(auto_now=True)
	
class BusinessBetaRequest(db.Model):
	business_name	= db.StringProperty()
	contact_name	= db.StringProperty()
	contact_email	= db.StringProperty()
	contact_phone	= db.StringProperty()
	date_created	= db.DateTimeProperty(auto_now_add=True)

