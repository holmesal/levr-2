import json
import levr_encrypt as enc
import levr_classes as levr
import logging
import os
import geo.geohash as geohash
from datetime import datetime

from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import urlfetch
from math import sin, cos, asin, sqrt, degrees, radians, floor, sqrt
from fnmatch import filter


#creates a url for remote or local server
if os.environ['SERVER_SOFTWARE'].startswith('Development') == True:
	#we are on the development environment
	host_url = 'http://localhost:8080/'
else:
	#we are deployed on the server
	host_url = 'http://www.levr.com/'



def send_error(self,error):
	reply = {
			'meta':{
				'success':False,
				'error':error
			},
			'alerts':{},
			'response':{}
	}
	logging.debug(levr.log_dict(reply))
	self.response.out.write(json.dumps(reply))
	
	
def check_search_inputs(self,lat,lon,limit):
	
	#check geopoint
	try:
		geo_string = str(lat)+","+str(lon)
		geo_point = levr.geo_converter(geo_string)
	except:
		self.send_error(self,'Invalid parameter: lat or lon'+geo_string)
		return (False,None,None)
	
	if limit != '':
		#limit was passed, so check if it is integer
		if not limit.isdigit():
			#limit fails, return false
			self.send_error(self,'Invalid parameter: limit'+str(limit))
			return (False,None,None)
	else:
		#limit was not passed, set to default
		limit = None
	
	return (True,geo_point,limit)
	
	
def check_param(self,parameter,parameter_name,param_type='str',required=True):
	#check if parameter sent in params
	#parameter is passed
	logging.info(parameter_name+": "+str(parameter))
	if not parameter:
#		logging.info("EERRRRR")
		#parameter is empty
#		if required == True:
#			send_error(self,'Required parameter not passed: '+str(parameter_name))
		return False
	else:
		#parameter is not empty
		#if parameter is an entity key, make sure
		if param_type == 'key':
#			logging.info('key')
			#parameter is an entity key
			try:
#				logging.info('start test key')
#				logging.debug(parameter)
				parameter = enc.decrypt_key(parameter)
#				logging.debug(parameter)
				parameter = db.Key(parameter)
#				logging.debug(parameter)
#				logging.debug('end test key')
			except:
#				if required == True:
#					send_error(self,'Invalid parameter: '+str(parameter_name)+"; "+str(parameter))
				return False
		elif param_type == 'int':
#			logging.debug('integer')
			if not parameter.isdigit():
#				if required == True:
#					send_error(self,'Invalid parameter: '+str(parameter_name)+"; "+str(parameter))
#				else:
				logging.error('Flag parameter: '+str(parameter))
				return False
	logging.info(parameter_name+": "+str(parameter))
	return True

def package_deal(deal,private=False,externalBusiness=None,externalID=None,*args,**kwargs):
	
	#if externalBusiness, business came from an external source, use that instead of a datastore-fetched deal
	if externalBusiness:
		packaged_business = externalBusiness
	#otherwise, business came from an internal source, go grab it from the datastore
	else:
		packaged_business = package_business(levr.Business.get(deal.businessID))
	
	#if externalID, deal came from an external source, use that ID to identify it
	if externalID:
		dealID = externalID
	#otherwise, the deal came from the datastore, use the key as the ID
	else:
		dealID = enc.encrypt_key(deal.key())

#	logging.debug(str(deal.geo_point))
	packaged_deal = {
# 			'barcodeImg'	: deal.barcode,
			'business'		: packaged_business,
 			'dateUploaded'	: str(deal.date_uploaded)[:19],
			'dealID'		: dealID,
			'dealText'		: deal.deal_text,
			'description'	: deal.description,
			'largeImg'		: create_img_url(deal,'large'),
			'smallImg'		: create_img_url(deal,'small'),
			'status'		: deal.deal_status,
			'shareURL'		: create_share_url(deal),
			'tags'			: deal.tags,
# 			'dateEnd'		: str(deal.date_end)[:19],
			'vote'			: deal.upvotes - deal.downvotes,
			'pinColor'		: deal.pin_color,
			'karma'			: deal.karma,
			'origin'		: deal.origin
			}
	
	rank = kwargs.get('rank')
	if rank: packaged_deal['rank'] = rank
	
	logging.debug('rank')
	logging.debug(kwargs.get('rank'))
	if deal.is_exclusive == False:
		packaged_deal.update({
			'owner'			: package_user(levr.Customer.get(deal.key().parent()))
		})
	
	if private == True:
		packaged_deal.update({
							})
		
	return packaged_deal
def package_user(user,private=False,followers=True,**kwargs):
	
	packaged_user = {
		'uid'			: enc.encrypt_key(str(user.key())),
		'alias'			: user.display_name,
		'dateCreated'	: user.date_created.__str__()[:19],
		'firstName'		: user.first_name,
		'lastName'		: user.last_name,
		'photoURL'		: user.photo,
		'level'			: user.level,
		'karma'			: user.karma,
		'twitterScreenName'	: user.twitter_screen_name,
		'email'			: user.email
		}
	if followers == True:
		followers_list = levr.Customer.get(user.followers)
		packaged_user['followers'] = [package_user(f,True,False) for f in followers_list]
	
	#check if the token will be sent with the response
	send_token = kwargs.get('send_token')
	if send_token:
		packaged_user.update({
							'levrToken': user.levr_token
							})
	
# 	if private:
# 		packaged_user.update({
# 							'moneyAvailable'	: 1,
# 							'moneyEarned'		: 1,
# 							})
	
	return packaged_user
def package_notification(notification):
	packaged_notification = {
		'notificationID'	: enc.encrypt_key(str(notification.key())),
#		'date'				: str(notification.date)[:19],
		'date'				: notification.date_in_seconds,
		'notificationType'	: notification.notification_type,
		'line2'				: notification.line2,
		'user'				: package_user(notification.actor),
		'notificationID'	: enc.encrypt_key(notification.key())
		}
	if notification.deal:
		packaged_notification['deal'] = package_deal(notification.deal)
	
	return packaged_notification
	
def package_business(business,externalID=None):
	#if this deal came from an external service, give it the ID that the external service gave it
	if externalID:
		businessID = externalID
	#otherwise this deal comes from the datastore (has a key) - encrypt it	
	else:	
		businessID = enc.encrypt_key(str(business.key()))
	
	
		

	packaged_business = {
		'businessID'	: businessID,
		'businessName'	: business.business_name,
		'vicinity'		: business.vicinity,
		'geoPoint'		: str(business.geo_point),
		'geoHash'		: business.geo_hash
						}
						
	if business.owner:
		packaged_business.update({
			'owner':	levr_utils.package_user(business.owner)
		})
	return packaged_business
	
def send_response(self,response,user=None):
	'''The optional third argument should be passed a user object if this is a private response
		and left out if a public response '''
	#build meta object
	meta = {'success':True}
	
	#build alerts object		
	#only send back alerts with private (user-authenticated) responses (optional parameter user)
	if user != None:
		alerts = {'newNotifications':user.new_notifications}
	else:
		alerts = {'newNotifications':0}
	
	#build reply object
	reply = {'meta':meta,
				'alerts':alerts,
				'response':response}
				
	#reply
	logging.debug(levr.log_dict(reply))
	self.response.out.write(json.dumps(reply))
	


def create_share_url(deal_entity):
	#creates a share url for a deal
	share_url = host_url+deal_entity.share_id
	return share_url
	
def create_img_url(entity,size):
	#creates a url that will serve the deals image
#	logging.debug(levr.log_dir(entity))
#	logging.debug(entity.class_name())
#	logging.debug(type(entity.kind()))
	
#	logging.debug(entity.kind())
#	logging.debug(entity.kind() == 'Deal')
	if entity.kind() == 'Customer':
		hook = 'api/user/'
	elif entity.kind() == 'Deal':
		hook = 'api/deal/'
	else:
		raise KeyError('entity does not have an image: '+entity.kind())
	
	#create one glorious url
	img_url = host_url+hook+enc.encrypt_key(entity.key())+'/img?size='+size
	return img_url

def private(handler_method):
	'''
	Decorator used to reject calls that require private auth and do not have them
	'''
	def check(self,*args,**kwargs):
		try:
			logging.debug('PRIVATE SCREENING DECORATOR\n\n\n')
			logging.debug(args)
			logging.debug(kwargs)
			
			private = kwargs.get('private')
			
			if private:
				#RPC is authorized
				handler_method(self,*args,**kwargs)
			else:
				#call is unauthorized - reject
				send_error(self,'Not Authorized')
			
			
			
		except Exception,e:
			levr.log_error()
			send_error(self,'Server Error')
			
	
	return check

def validate(url_param,authentication_source,*a,**to_validate):
	'''
	General function for validating the inputs that are passed as arguments
	to use, pass kwargs in form of key:bool,
	where key is the input name and bool is true if input is required and false if input is optional
	'''
	
	def wrapper(handler_method):
		'''
		This is the decorator that operates on the function being decorated
		I dont understand this. Gah!
		'''
		def validator(self,*args,**kwargs):
			logging.debug('Validator')
			logging.debug(args)
			if args: logging.debug('yes')
			logging.debug(kwargs)
			logging.debug(a)
			if a: logging.debug('WWOOO')
			else: logging.debug('NOOO')
			logging.debug("to_validate: "+str(to_validate))
#			logging.debug(name)
			logging.debug("auth_source: "+str(authentication_source))
			
			type_cast = {
						'user'		: levr.Customer,
						'deal'		: levr.Deal,
						
						#searching, user info, deal info stuff
						'limit'		: int,
						'offset'	: int,
						'geoPoint'	: db.GeoPt,
						'radius'	: float,
						'since'		: int,
						'size'		: str,
						
						#login stuff
						'levrToken'		: str,
						'facebookID'	: str,
						'token'			: str,
						'screenName'	: str,
						'email_or_owner': str,
						'pw'			: str,
						
						#deal upload stuff
						'description'	: str,
						'dealText'		: str,
						'distance'		: float,
						
						#business upload stuff
						'businessName'	: str,
						#geoPoint ^^ see above
						'vicinity'		: str,
						'types'			: str,
						'shareURL'		: str
						}
			defaults = {
						#entities
						'user'		: None,
						'deal'		: None,
						
						#searching, user info, deal info stuff
						'limit'		: 50,
						'offset'	: 0,
						'geoPoint'	: levr.geo_converter('42.349798,-71.120000'),
						'radius'	: 2,
						'since'		: None,
						'size'		: 'large',
						'query'		: 'all',
						
						#login stuff
						'levrToken'			: '',
						'facebookID'		: '',
						'token'				: '',
						'screenName'		: '',
						'email_or_owner'	: '',
						'pw'				: '',
						
						#deal upload stuff
						'description'	: '',
						'dealText'		: '',
						'distance'		: -1,
						
						#business upload stuff
						'businessName'	: '',
						'vicinity'		: '',
						'types'			: '',
						'shareURL'		: ''
						}
			
			try:
				####################################################
				#Validate the input passed in the url, not as param#
				####################################################
				
				logging.debug("url_param: "+str(url_param))
				
				if url_param == 'deal':
					#A dealID is passed as part of the url
					
					#if no dealID is passed, report it missing
					try: dealID = args[0]
					except: KeyError('dealID')
					
					#assure the validitity of the dealID
					try:
						dealID = enc.decrypt_key(dealID)
						deal = levr.Deal.get(dealID)
						
						#pass the deal object, not the id, to the handler
						kwargs.update({'deal':deal})
					except:
						levr.log_error()
						raise TypeError('dealID: '+str(enc.encrypt_key(dealID)))
					
					
				elif url_param == 'user':
					#A uid is passed as part of the url
					
					#if no uid is passed, report it missing
					try: uid = args[0]
					except: KeyError('uid')
					
					
					#assure the validity of the uid
					try:
						uid = enc.decrypt_key(uid)
						user = levr.Customer.get(uid)
						#pass the user OBJECT, not the id, to the handler
						kwargs.update({'user':user})
					except Exception,e:
						levr.log_error()
						raise TypeError('uid: '+str(enc.encrypt_key(uid)))
				
				
				elif url_param == 'query':
					#a query is passed as part of the url
					
					#check that there is a query there
					try:
						query = args[0]
						
						#if query is empty, set to default query
						if not query:
							query = defaults['query']
							
						#pass query to the handler
						kwargs.update({'query':query})
					except:
						levr.log_error('Check validator call. "query" should not be passed as a param if there is no variable regex in the url declaration')
						TypeError('query: None')
				
				elif url_param == None:
					#nothing is passed to the handler as part of the url
					pass
				else:
					raise Exception('Invalid url_param')
				
				
				
				
				###########################
				#Start user authentication#
				###########################
				
				#If the user needs to be validated, validation source will be passed to the decorator
				if not authentication_source:
					#No validation is required, and privacy is automatically set to public
					private = False
				else:
					#This needs to be nested in t
					#validation is required
					if authentication_source == 'url':
						logging.debug('authenticate in url')
						#the user that needs to be validated is passed as part of the url, i.e. /api/user/<uid>/action
						#the user has already been fetched by the above block of code
						if url_param != 'user': raise Exception('Doh! Check validation decorator decoration')
						
					elif authentication_source == 'param':
						#the user that needs to be validated is passed as a param i.e. /api/deal/<dealID>/upvote?uid=UID
						logging.debug('authenticate in parameter')
						#get the uid, and the kwarg that tells us if it is required
						uid = self.request.get('uid')
						required = to_validate.get('user')
						
						logging.debug(uid)
						logging.debug(required)
						
						if not uid and required: raise KeyError('uid')
						if not uid and not required: 
							#handle this elsewhere
							user = None
						else:
							#uid was passed, so validate it!
							try:
								logging.debug('hi')
								#translate uid into a db.Key type
								uid = db.Key(enc.decrypt_key(uid))
								#get the user - constrains to user kind
								user = levr.Customer.get(uid)
							except:
								raise TypeError('uid: '+ str(enc.encrypt_key(uid)))
							
						
					else:
						raise Exception('Invalid validation source')
					
					
					#check token validity
					#assure that the token was passed
					levr_token = self.request.get('levrToken')
					logging.debug(levr_token)
					#check token against stored token
					if user:
						if levr_token == user.levr_token	: private = True
						else								: private = False
					else:
						private = False
					
					
					
					#compare the passed token to the db token
					#if token checks out, the private is True
					
					
				logging.debug(private)
				
				
				#update kwargs to include privacy level
				kwargs.update({'private':private})
					
				
				##################################
				#start parameter validation steps#
				##################################
				
				
				#for each input=Bool where Bool is required or not
				for (key,required) in to_validate.iteritems():
					#special case, geopoint is complex
					if key == 'geoPoint':
						val = str(self.request.get('lat'))+","+str(self.request.get('lon'))
						msg = "lat,lon: "+val
					
					elif key == 'user':
						val = self.request.get('uid')
						msg = 'uid: '+ val
					
					elif key == 'deal':
						val = self.request.get('dealID')
						msg = 'dealID: '+ val
					#common mistakes. Youre welcome, debugger.
					elif key == 'uid'		: raise Exception('In validation declaration, "uid" should be "user".')
					elif key == 'dealID'	: raise Exception('In validation declaration, "dealID" should be "deal"')
					#default case
					else:
						val = self.request.get(key)
						msg = key+": "+val
					logging.debug(val)
					#requires is whether or not it is required
					required	= to_validate.get(key)
					#date_type pulls the type that the passed input should be
					try:
						data_type	= type_cast[key]
					except:
						levr.log_error('did not map type_cast dict correctly')
						raise Exception()
					#msg is passed to the exception handler if val fails validation
					
#					logging.debug(key)
#					logging.debug(val)
					logging.debug(msg)
					logging.debug(data_type)
					logging.debug(required)
					
					#handle case where input is not passed
					
					if 		not val and required				: raise KeyError(msg)
					elif 	not val and not required			: val = defaults[key]
					
					#handle case where input should be an integer
					elif data_type == int: 
						if val.isdigit():
							#translate input from unicode to int
							val = int(val)
							
						else:
							levr.log_error()
							raise TypeError(msg)
					#handle case where input should be numerical 
					elif data_type == float:
						#float input
						try:
							val = float(val)
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg)
					elif data_type == db.GeoPt:
						try:
							logging.debug(val)
							val = levr.geo_converter(val)
							logging.debug(val)
							logging.debug(type(val))
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg)
					elif data_type == levr.Customer:
						try:
							#convert to key
							val = db.Key(enc.decrypt_key(val))
							
							#get user entity
							user = levr.Customer.get(val)
							
							val = user
							key = 'actor'
							
							#send test flag
							if user.tester: kwargs.update({'development':True})
							else: kwargs.update({'development':False})
							
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg)
					elif data_type == levr.Deal:
						try:
							val = db.Key(enc.decrypt_key(val))
							
							deal = levr.Deal.get(val)
							
							val = deal
							
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg)
					elif data_type == list:
						try:
							val = val.split(',')
							logging.debug(val)
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg+"... must be a comma delimited string")
					elif data_type == str:
						pass
						
					#update the dictionary that is passed to the handler function with the key:val pair
					kwargs.update({key:val})
				
				logging.debug(kwargs)
			
			except AttributeError,e:
				levr.log_error()
				send_error(self,'Not Authorized, '+str(e))
			except KeyError,e:
				levr.log_error()
				send_error(self,'Required paramter not passed, '+str(e))
			except TypeError,e:
				levr.log_error()
				
				send_error(self,'Invalid parameter, '+str(e))
			except Exception,e:
				levr.log_error()
				send_error(self,'Server Error: '+str(e))
			else:
				return handler_method(self,*args,**kwargs)
		
		return validator
	
	return wrapper

def send_img(self,blob_key,size):
	try:
		logging.debug(levr.log_dir(blob_key.properties))
		
		
		#read the blob data into a string !!!! important !!!!
		blob_data = blob_key.open().read()
		
		#pass blob data to the image handler
		img			= images.Image(blob_data)
		#get img dimensions
		img_width	= img.width
		img_height	= img.height
		logging.debug(img_width)
		logging.debug(img_height)
		
		#define output parameters
		if size == 'large':
			#view for top of deal screen
			aspect_ratio 	= 3. 	#width/height
			output_width 	= 640.	#arbitrary standard
		elif size == 'small':
			#view for in deal or favorites list
			aspect_ratio	= 1.	#width/height
			output_width	= 200.	#arbitrary standard
		elif size == 'dealDetail':
			#view for top of deal screen
			aspect_ratio 	= 3. 	#width/height
			output_width 	= 640.	#arbitrary standard
		elif size == 'list':
			#view for in deal or favorites list
			aspect_ratio	= 1.	#width/height
			output_width	= 200.	#arbitrary standard
		elif size == 'fullSize':
			#full size image
			aspect_ratio	= float(img_width)/float(img_height)
			output_width	= float(img_width)
	#			self.response.out.write(deal.img)
		elif size == 'webShare':
			aspect_ratio	= 4.
			output_width	= 600.
		elif size == 'facebook':
			aspect_ratio 	= 1.
			output_width	= 250.
		elif size == 'emptySet':
			aspect_ratio	= 3.
			output_width	= 640.
		elif size == 'widget':
			aspect_ratio	= 1.
			output_width	= 150.
		else:
			raise KeyError('Invalid image size: '+size)
		
			
			##set this to some default for production
		#calculate output_height from output_width
		output_height	= output_width/aspect_ratio
		
		##get crop dimensions
		if img_width > img_height*aspect_ratio:
			#width must be cropped
			w_crop_unscaled = (img_width-img_height*aspect_ratio)/2
			w_crop 	= float(w_crop_unscaled/img_width)
			left_x 	= w_crop
			right_x = 1.-w_crop
			top_y	= 0.
			bot_y	= 1.
		else:
			#height must be cropped
			h_crop_unscaled = (img_height-img_width/aspect_ratio)/2
			h_crop	= float(h_crop_unscaled/img_height)
			left_x	= 0.
			right_x	= 1.
			top_y	= h_crop
			bot_y	= 1.-h_crop
	
		#crop image to aspect ratio
		img.crop(left_x,top_y,right_x,bot_y)
		logging.debug(img)
		
		#resize cropped image
		img.resize(width=int(output_width),height=int(output_height))
		logging.debug(img)
		
		#package image
		output_img = img.execute_transforms(output_encoding=images.JPEG)
		
		#write image to output
		self.response.headers['Content-Type'] = 'image/jpeg'
		self.response.out.write(output_img)
		
	except KeyError,e:
		send_error(self,e)
	except Exception,e:
		levr.log_error(e)
		send_error(self,'Server Error')
	
	
def get_deal_keys_from_hash_set(tags,hash_set,*args,**kwargs):
	'''
	Returns a list of deal keys in the hash sets specified
	
	tags = list of tags that are strings
	request point is db.GeoPt format
	
	optional parameters:
	development		default=False
	
	'''
	
	#grab variables
	development		= kwargs.get('development',False)
	if development:
		#developer is searching
		deal_status = 'test'
		logging.debug('test deals')
	else:
		#a real person is searching!
		deal_status = 'active'
		logging.debug('active deals')
	
	SPECIAL_QUERIES = ['all','popular','new','hot']
	
	
	####build search query
	deal_keys = []
	for query_hash in hash_set:
		#initialize query
		q = levr.Deal.all(keys_only=True)
		
		#if a real deal, status is active
		if not development:
			q.filter('deal_status =','active')
#			logging.debug('flag active')
		else:
			q.filter('deal_status =','test')
#			logging.debug('flag development')
		
#		logging.debug("tags: "+str(tags))
		#FILTER BY TAG
		#do not filter by tags if the tag is one of the special key words
		if tags and tags[0] not in SPECIAL_QUERIES:
			#grab all deals where primary_cat is in tags
			for tag in tags:
				logging.debug('tag: '+str(tag))
				q.filter('tags =',tag)
		else:
			pass
#			logging.debug('This is a special case. Not filtering by tags: '+str(tags))
		
		
		#grab all deals in the geohash
		q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
#					logging.debug(q)
#		logging.debug(levr.log_dict(q.__dict__))
		
		
		#FETCH DEAL KEYS
		fetched_deals = q.fetch(None)
		logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
		
		#add to the list
		deal_keys.extend(fetched_deals)
	
	return deal_keys

def filter_deals_by_radius(deals,center,radius):
	'''
	http://stackoverflow.com/questions/3182260/python-geocode-filtering-by-distance
	'''
	logging.debug('FILTER BY RADIUS')
	#Only returns deals that are within a radius of the center
	
	
	
	
	#get the geopoints of all deals
	
	#create list of deals to be returned
	acceptable_deals = []
	
	#parse center geo_point into lat, lon
	lat1 = center.lat
	lon1 = center.lon
	
	#convert radius to float for comparison to work
	if type(radius) != float:
		radius = float(radius)
	
	
	for deal in deals:
		#parse geo_point into lat,lon
		lat2 = deal.geo_point.lat
		lon2 = deal.geo_point.lon
		
		#calculate distance
		distance = distance_between_points(lat1,lon1,lat2,lon2)
		if distance < radius:
			#append deal to output deals
			acceptable_deals.append(deal)
#		else:
#			logging.debug('False')
#			logging.debug(distance)
	
	return acceptable_deals

#######GEO DISTANCES
Earth_radius_km = 6371.0
RADIUS = Earth_radius_km
def haversine(angle_radians):
	return sin(angle_radians / 2.0) ** 2

def inverse_haversine(h):
	return 2 * asin(sqrt(h)) # radians

def distance_between_points(lat1, lon1, lat2, lon2):
	# all args are in degrees
	# WARNING: loss of absolute precision when points are near-antipodal
	lat1 = radians(lat1)
	lat2 = radians(lat2)
	dlat = lat2 - lat1
	dlon = radians(lon2 - lon1)
	h = haversine(dlat) + cos(lat1) * cos(lat2) * haversine(dlon)
	return RADIUS * inverse_haversine(h)

def bounding_box(lat, lon, distance):
	# Input and output lats/longs are in degrees.
	# Distance arg must be in same units as RADIUS.
	# Returns (dlat, dlon) such that
	# no points outside lat +/- dlat or outside lon +/- dlon
	# are <= "distance" from the (lat, lon) point.
	# Derived from: http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
	# WARNING: problems if North/South Pole is in circle of interest
	# WARNING: problems if longitude meridian +/-180 degrees intersects circle of interest
	# See quoted article for how to detect and overcome the above problems.
	# Note: the result is independent of the longitude of the central point, so the
	# "lon" arg is not used.
	dlat = distance / RADIUS
	dlon = asin(sin(dlat) / cos(radians(lat)))
	return degrees(dlat), degrees(dlon)
##########/GEO DISTANCES


def level_check(user):
	'''updates the level of a user. this function should be run after someone upvotes a user or anything else happens.'''
	'''square root for the win'''
	old_level = user.level
	new_level = int(floor(sqrt(user.karma)))
	
	if new_level != old_level:
		#level up notification
		levr.create_notification('levelup',user.key(),user.key())
		
	user.level = new_level
		
	return user

def search_yipit(query,geo_point):
	words = ["a la carte","a la mode","appetizer","beef","beverage","bill","bistro","boiled","bowl","braised","bread","breakfast","brunch","butter","cafe","cafeteria","cake","candle","cashier","centerpiece","chair","charge","chef","chicken","coffee","cola","cold","condiments","cook","cooked","course","cream","credit card","cutlery","deli","delicatessen","delicious","dessert","dine","diner","dining","dinner","dish","dishwasher","doggie bag","dressing","eat","eggs","entree","fish","food","fork","French fries","fries","fruit","glass","gourmand","gourmet","grilled","hamburger","head waiter","high tea","hors d'oeuvre","hostess","hot","ice","ice cubes","iced","ingredients","ketchup","kitchen","knife","lemonade","lettuce","lunch","main course","maitre d'","manager","meal","meat","medium","menu","milk","mug","mustard","napkin","noodles","onion","order","party","pasta","pepper","plate","platter","pop","rare","reservation","restaurant","roasted","roll","salad","salt","sandwich","sauce","saucer","seafood","seared","server","side order","silverware","soda","soup","special","spices","spicy","spill","spoon","starters","steak","sugar","supper","table","tablecloth","tasty","tax","tea","tip","toast","to go","tomato","utensils","vegetables","waiter","waitress","water","well-done"]
	
	#if query in words:
	if True:
		#search for restaurants
		logging.info(str(geo_point))
		#search_lat, search_lng = geo_point.split(',')
		search_lat = geo_point.lat
		search_lon = geo_point.lon
		#url = 'http://api.yipit.com/v1/deals/?key=d9qcYtHgkKcPTAGD&tag=restaurants&lat='+lat+'&lon='+lon
		url = 'http://api.yipit.com/v1/deals/?key=d9qcYtHgkKcPTAGD&tag=restaurants&lat='+str(search_lat)+'&lon='+str(search_lon)
		logging.info(url)
		result = urlfetch.fetch(url=url)
		result = json.loads(result.content)['response']
		deals = result['deals']
		
		packaged_deals = []
		
		for yipit_deal in deals:
			
			yipit_business = yipit_deal['business']
			
			lat = yipit_business['locations'][0]['lat']
			lon = yipit_business['locations'][0]['lon']
			
			if lat==None or lon==None:
				pass
			else:
			
				business = levr.Business()
				business.business_name = yipit_business['name']
				business.vicinity = yipit_business['locations'][0]['address'] + ', ' + yipit_business['locations'][0]['locality']
				business.geo_point = levr.geo_converter(str(lat)+','+str(lon))
				business.geo_hash = geohash.encode(lat,lon)
				
				packaged_business = api_utils.package_business(business,'yipitdoesnotuseidsforbusinesses')
				
				deal = levr.Deal()
				deal.deal_text = yipit_deal['yipit_title']
				deal.description = ''
				deal.largeImg = yipit_deal['images']['image_big']
				deal.smallImg = yipit_deal['images']['image_small']
				deal.status = 'active'
				
				
				packaged_deal = api_utils.package_deal(deal,False,business,yipit_deal['id'])
			
				# packaged_business = {
# 				'businessName'		:	business['name'],
# 				'vicinity'			:	business['locations'][0]['address'] + ', ' + business['locations'][0]['locality'],
# 				'geoPoint'			:	str(lat)+','+str(lon),
# 				'geoHash'			:	geohash.encode(lat,lon)
# 				}
			
# 				logging.info(packaged_business)
				
				packaged_deal = {
				#barcode image
				'business'			: packaged_business,
				#date uploaded
				#dealID
				'dealText'			: deal['yipit_title'],
				#description
				#isExclusive
				'largeImg'			: deal['images']['image_big'],
				'smallImg'			: deal['images']['image_small'],
				'shareURL'			: deal['yipit_url'],
				'tags'				: 'restaurants',
				'pinColor'			: '255,255,255',
				'externalLink'		: deal['mobile_url'],
				'attributionText'	: 'Powered by:',
				'attributionImage'	: 'http://farm6.static.flickr.com/5205/5281647796_c42d9b6a15.jpg',
				'attributionLink'	: 'http://www.yipit.com'
				}
				
				
				packaged_deals.append(packaged_deal)
				
		logging.info(packaged_deals)
		return packaged_deals
# 			
# 				#build a deal
# 				deal = levr.Deal()
# 			
# 		def package_business(business):
# 	packaged_business = {
# 		'businessID'	: enc.encrypt_key(str(business.key())),
# 		'businessName'	: business.business_name,
# 		'vicinity'		: business.vicinity,
# 		'foursquareID'	: business.foursquare_id,
# 		'foursquareName': business.foursquare_name,
# 		'geoPoint'		: str(business.geo_point),
# 		'geoHash'		: business.geo_hash
# 						}
# 		
# 		packaged_deal = {
# 			'barcodeImg'	: deal.barcode,
# 			'business'		: package_business(levr.Business.get(deal.businessID)),
# 			'dateUploaded'	: str(deal.date_end)[:19],
# 			'dealID'		: enc.encrypt_key(deal.key()),
# 			'dealText'		: deal.deal_text,
# 			'description'	: deal.description,
# 			'isExclusive'	: deal.is_exclusive,
# 			'largeImg'		: create_img_url(deal,'large'),
# 			'redemptions'	: deal.count_redeemed,
# 			'smallImg'		: create_img_url(deal,'small'),
# 			'status'		: deal.deal_status,
# 			'shareURL'		: create_share_url(deal),
# 			'tags'			: deal.tags,
# 			'dateEnd'		: str(deal.date_end)[:19],
# 			'vote'			: deal.upvotes - deal.downvotes,
# 			'pinColor'		: deal.pin_color,
# 			'karma'			: deal.karma
# 			}
# 			
# 			
	else:
		return False

def search_foursquare(self,geo_point,user):
# 	try:
	#user must be connected with foursquare to be able to access these specials
	#go get the user's foursquare token
	token = user.foursquare_token
	#form the url
	url = 'https://api.foursquare.com/v2/specials/search?v=20120920&ll='+str(geo_point)+'&limit=50&oauth_token='+token
	result = urlfetch.fetch(url=url)
	result = json.loads(result.content)
	foursquare_deals = result['response']['specials']['items']
	
	allowed_categories = ["Afghan Restaurant", "African Restaurant", "American Restaurant", "Arepa Restaurant", "Argentinian Restaurant", "Asian Restaurant", "Australian Restaurant", "BBQ Joint", "Bagel Shop", "Bakery", "Brazilian Restaurant", "Breakfast Spot", "Brewery", "Burger Joint", "Burrito Place", "Caf\u00e9", "Cajun / Creole Restaurant", "Caribbean Restaurant", "Chinese Restaurant", "Coffee Shop", "Cuban Restaurant", "Cupcake Shop", "Deli / Bodega", "Dessert Shop", "Dim Sum Restaurant", "Diner", "Distillery", "Donut Shop", "Dumpling Restaurant", "Eastern European Restaurant", "Ethiopian Restaurant", "Falafel Restaurant", "Fast Food Restaurant", "Filipino Restaurant", "Fish & Chips Shop", "Food Truck", "French Restaurant", "Fried Chicken Joint", "Gastropub", "German Restaurant", "Gluten-free Restaurant", "Greek Restaurant", "Hot Dog Joint", "Ice Cream Shop", "Indian Restaurant", "Indonesian Restaurant", "Italian Restaurant", "Japanese Restaurant", "Juice Bar", "Korean Restaurant", "Latin American Restaurant", "Mac & Cheese Joint", "Malaysian Restaurant", "Mediterranean Restaurant", "Mexican Restaurant", "Middle Eastern Restaurant", "Molecular Gastronomy Restaurant", "Mongolian Restaurant", "Moroccan Restaurant", "New American Restaurant", "Peruvian Restaurant", "Pizza Place", "Portuguese Restaurant", "Ramen / Noodle House", "Restaurant", "Salad Place", "Sandwich Place", "Scandinavian Restaurant", "Seafood Restaurant", "Snack Place", "Soup Place", "South American Restaurant", "Southern / Soul Food Restaurant", "Spanish Restaurant", "Steakhouse", "Sushi Restaurant", "Swiss Restaurant", "Taco Place", "Tapas Restaurant", "Tea Room", "Thai Restaurant", "Turkish Restaurant", "Vegetarian / Vegan Restaurant", "Vietnamese Restaurant", "Winery", "Wings Joint", "Bar", "Beer Garden", "Cocktail Bar", "Dive Bar", "Gay Bar", "Hookah Bar", "Hotel Bar", "Karaoke Bar", "Lounge", "Nightclub", "Other Nightlife", "Pub", "Sake Bar", "Speakeasy", "Sports Bar", "Strip Club", "Whisky Bar", "Wine Bar"]
	
	allowed_types = ['count','regular','flash','swarm','other','frequency','mayor']
	
	for foursquare_deal in foursquare_deals:
		logging.info('woo a deal!')
		#logging.info(foursquare_deal['venue']['categories'][0]['name'])
		if foursquare_deal['venue']['categories'][0]['name'] in allowed_categories and foursquare_deal['type'] in allowed_types:
			logging.info(foursquare_deal['type'])
			logging.info(foursquare_deal['message'])
			logging.info(foursquare_deal['venue']['categories'][0]['name'])
			
			#does business already exist?
			existing_business = levr.Business.gql('WHERE foursquare_id=:1',foursquare_deal['venue']['id']).get()
			if not existing_business:
				venue = foursquare_deal['venue']
				business = levr.Business(
					business_name 		= 	venue['name'],
					foursquare_name		=	venue['name'],
					foursquare_id		=	venue['id'],
					vicinity			=	venue['location']['address'] + ', ' + venue['location']['city'],
					geo_point			=	db.GeoPt(venue['location']['lat'],venue['location']['lng']),
					geo_hash			=	geohash.encode(venue['location']['lat'],venue['location']['lng']),
					types				=	[venue['categories'][0]['name']]
				)
				business.put()
				logging.info(business.__dict__)
			else:
				logging.info('business already exists')
				business = existing_business
			
			
			
			#does deal already exist?
			existing_deal = levr.Deal.gql('WHERE foursquare_id=:1',foursquare_deal['id']).get()
			if not existing_deal:
				logging.info(foursquare_deal['message'])
				deal = levr.Deal(
					businessID		=	str(business.key()),
					deal_status		=	'active',
					tags			=	levr.tagger(foursquare_deal['message']+' '+foursquare_deal['description']+' '+foursquare_deal['venue']['name']+' '+foursquare_deal['venue']['categories'][0]['name']),
					origin			=	'foursquare',
					external_url	=	'THISISAFAKEURL',
					foursquare_id	=	foursquare_deal['id'],
					foursquare_type	=	foursquare_deal['venue']['categories'][0]['name'],
					deal_text		=	foursquare_deal['message'].rstrip('\n'),
					description		=	foursquare_deal['description'],
					geo_point		=	business.geo_point,
					geo_hash		=	business.geo_hash
				)
				
				logging.info(deal.__dict__)
			else:
				logging.info('deal already exists')
			
			
			
			
			
			#logging.info(foursquare_deal[''])
			
		#logging.info(foursquare_deal['state'])
			
# 			#is the deal already in the database?
# 			existing_deal = levr.Deal.gql('WHERE foursquare_id=:1',foursquare_deal['id']).get()
# 			
# 			if existing_deal:
# 				#this deal already exists, check if the status is different
# 				if existing_deal.status
				
		#self.response.out.write(result.content['response'])
		#result = json.loads(result.content)
#	except:
		#raise Exception('Error parsing foursquare response')
		#ask pat about error handling here
