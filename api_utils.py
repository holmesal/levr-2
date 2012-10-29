#from common_word_list import blacklist
from datetime import datetime
from google.appengine.api import images, urlfetch, memcache
from google.appengine.ext import db
from math import sin, cos, asin, degrees, radians, floor, sqrt
import api_utils_social as social
import geo.geohash as geohash
import json
import levr_classes as levr
import levr_encrypt as enc
import logging
import os
import random
import urllib
#from fnmatch import filter


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
	
	
	
	

def create_pin_color(deal):
	if deal.origin == 'levr':
		pin_color = 'red'
	elif deal.origin == 'foursquare':
		pin_color = 'blue'
	elif deal.origin == 'merchant':
		pin_color = 'green'
	else:
		pin_color = 'orange'
		
	return pin_color

def package_deal_multi(deals,private=False,*args,**kwargs):
	'''
	Batch packages a list of deals - prefetching related entities
	
	@param deals: The deal entities to be packaged for output
	@type deals: [levr.Deal,]
	@param private: Determines the privacy level of the information
	@type private: boolean
	'''
#	assert type(deals) == list, 'Must pass deals as a list; type = '+str(type(deals))
	
	# Remove deals that do not exist
	deals = filter(lambda x: x,deals)
	
	# deal meta information
	ranks = kwargs.get('ranks',[None for deal in deals]) #@UnusedVariable
	distances = kwargs.get('distances',[None for deal in deals]) #@UnusedVariable
	
	
	
	
	
	
	
	# prefetch deal owners
	owner_keys = [deal.key().parent() for deal in deals]
	owners = db.get(owner_keys)
	# prefetch deal businesses
	business_keys = [deal.businessID for deal in deals]
	businesses = db.get(business_keys)
	
	# Remove deals that have bad references...
	data = zip(deals,owners,businesses,ranks,distances)
	# Remove deals without valid owners
	data_sans_Nonetype_owners = filter(lambda x: x[1],data)
	# Remove deals without valid businesses
	new_data = filter(lambda x: x[2],data_sans_Nonetype_owners)
	
	# Notify the benevolent server monitors that there is some missing shit in here. BAD!
	if data != new_data:
		
		levr.log_error('There are deals with missing references: ')#+str([deal.key() for deal in deals]))
	
	
	# Continue without the filtered deals
	return package_prefetched_deal_multi(new_data, private)
	
def package_prefetched_deal_multi(data,private=False,*args,**kwargs):
	'''
	
	@param data: packaged deal information with prefetched related entities
	@type data: list of tuples: [(Deal,Customer,Business,int or None, float or None),]
	@param private: Set the data output level
	@type private: Boolean
	'''
	
	packaged_deals = []
	for point in data:
		# Unpack data
		deal,owner,business,rank,distance = point
		
		packaged_deal = _package_deal(deal, owner, business, private, rank, distance)
		packaged_deals.append(packaged_deal)
		
	return packaged_deals
def _package_deal(deal,owner,business,private=False,rank=None,distance=None):
	packaged_deal = {
	# 			'barcodeImg'	: deal.barcode,
				'business'		: package_business(business),
	 			'dateUploaded'	: str(deal.date_uploaded)[:19],
				'dealID'		: enc.encrypt_key(deal.key()),
				'dealText'		: deal.deal_text,
				'description'	: deal.description,
				'largeImg'		: create_img_url(deal,'large'),
				'smallImg'		: create_img_url(deal,'small'),
				'status'		: deal.deal_status,
				'shareURL'		: create_share_url(deal),
				'tags'			: deal.tags,
				'vote'			: deal.upvotes - deal.downvotes,
				'pinColor'		: create_pin_color(deal),
				'karma'			: deal.karma,
				'origin'		: deal.origin,
				'owner'			: package_user(owner,private,False)
				}
	
	if rank: packaged_deal['rank'] = rank
	if distance: packaged_deal['distance'] = distance
	
	if private == True:
		packaged_deal.update({
							'views'	: deal.views
							})
	
	return packaged_deal
	
def package_deal(deal,private=False,*args,**kwargs):
#	logging.debug(deal.businessID)
#	logging.debug(deal.key())
#	logging.debug(str(deal.geo_point))
	rank = kwargs.get('rank',None)
	distance = kwargs.get('distance',None)
	
	owner = levr.Customer.get(deal.key().parent())
	business = levr.Business.get(deal.businessID)
	
	
	return _package_deal(deal, owner, business, private, rank, distance)
	
def package_deal_external(externalDeal,externalBusiness,fake_owner):
	
	packaged_deal = {
# 			'barcodeImg'	: deal.barcode,
			'business'		: externalBusiness,
			'dealID'		: externalDeal.externalID,
			'dealText'		: externalDeal.deal_text,
			'description'	: externalDeal.description,
			'largeImg'		: externalDeal.large_img,
			'smallImg'		: externalDeal.small_img,
			'pinColor'		: externalDeal.pin_color,
			'origin'		: externalDeal.origin,
			'externalURL'	: externalDeal.externalURL,
			'owner'			: fake_owner #externalAPI
			}
	
	return packaged_deal

def package_user(user,private=False,followers=False,**kwargs):

	# logging.debug(levr.log_model_props(user))
	
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
		
	if notification.notification_type == 'levelup':
		packaged_notification['user']['alias'] = 'Level up!'
	
	return packaged_notification
	
def package_business(business):

	packaged_business = {
		'businessID'	: enc.encrypt_key(str(business.key())),
		'foursquareID'	: business.foursquare_id,
		'businessName'	: business.business_name,
		'vicinity'		: business.vicinity,
		'geoPoint'		: str(business.geo_point),
		'geoHash'		: business.geo_hash
						}
						
	if business.owner:
		packaged_business.update({
			'owner':	package_user(business.owner)
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
	logging.debug(str(self.response.headers))


def create_share_url(deal_entity):
	#creates a share url for a deal
	share_url = host_url+deal_entity.share_id
	#logging.info('share url: '+share_url)
	return share_url
	
def create_img_url(entity,size):
	#creates a url that will serve the deals image
	# logging.debug(levr.log_dir(entity))
# 	logging.debug(entity.class_name())
# 	logging.debug(type(entity.kind()))
	
#	logging.debug(entity.kind())
# 	logging.debug(entity.kind() == 'Deal')
	# if entity.kind() == 'Customer':
#  		hook = 'api/user/'
	if entity.kind() == 'Deal':		hook = 'api/deal/'
	# else:
#  		raise KeyError('entity does not have an image: '+entity.kind())

	if entity.img:	
		#create one glorious url
		img_url = host_url+hook+enc.encrypt_key(entity.key())+'/img?size='+size
		return img_url
	if entity.foursquare_id and size=='small':
		return 'http://playfoursquare.s3.amazonaws.com/press/logo/icon-512x512.png'
	else:
		return ''


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
			levr.log_error(e)
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
		- it is produced by the higher level factory, 'validate'
		'''
		def validator(self,*args,**kwargs):
			logging.info('Validator')
			logging.debug("to_validate: "+str(to_validate))
			logging.debug("auth_source: "+str(authentication_source))
			
			type_cast = {
						'user'			: levr.Customer,
						'deal'			: levr.Deal,
						'business'		: levr.Business,
						'development'	: bool,
						
						#searching, user info, deal info stuff
						'limit'				: int,
						'offset'			: int,
						'geoPoint'			: db.GeoPt, #want to phase this out
						'll'				: db.GeoPt,
						'radius'			: float,
						'since'				: int,
						'size'				: str,
						'query'				: str,
						'latitudeHalfDelta' : float,
						'longitudeHalfDelta': float,
						
						
						#login and connect stuff
						'levrToken'			: str,
						'remoteToken'		: str, #oauth/access tokens for facebook, foursquare, etc...
						'remoteTokenSecret'	: str, #oauth token secret
						'remoteID'			: str, #e.g. facebook_id, foursquare_id, etc...
						'email_or_owner'	: str,
						'email'				: str,
						'pw'				: str,
						'alias'				: str,
						
						#deal upload stuff
						'description'	: str,
						'dealText'		: str,
						'distance'		: float,
						'action'		: str,
						
						#business upload stuff
						'businessName'	: str,
						#geoPoint ^^ see above
						'vicinity'		: str,
						'types'			: str,
						'shareURL'		: str,
						
						#promotion stuff
						'tags'			: list,
						'promotionID'	: str
						
						}
			defaults = {
						#entities
						'user'			: None,
						'deal'			: None,
						'business'		: None,
						'development'	: False,
						
						#searching, user info, deal info stuff
						'limit'				: 50,
						'offset'			: 0,
						'geoPoint'			: levr.geo_converter('42.349798,-71.120000'), #want to phase this out
						'll'				: levr.geo_converter('42.349798,-71.120000'),
						'radius'			: 2,
						'since'				: None,
						'size'				: 'large',
						'query'				: 'all',
						'latitudeHalfDelta'	: None,
						'longitudeHalfDelta': None,
						
						#login and connect stuff
						'levrToken'			: '',
						'remoteToken'		: '', #oauth/access tokens for facebook, foursquare, etc...
						'remoteTokenSecret'	: '', #oauth token secret
						'remoteID'			: '', #e.g. facebook_id, foursquare_id, etc...
						'email_or_owner'	: '',
						'email'				: '',
						'pw'				: '',
						'alias'				: '',
						
						#deal upload stuff
						'description'	: '',
						'dealText'		: '',
						'distance'		: -1,
						'action'		: '',
						
						#business upload stuff
						'businessName'	: '',
						'vicinity'		: '',
						'types'			: '',
						'shareURL'		: '',
						
						# Promotion stuff
						'tags'			: [],
						'promotionID'	: ''
						}
			
			try:
				#===============================================================
				# Validate the input passed in the url, not as param#
				#===============================================================
				
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
				elif url_param == 'contentID':
					try:
						contentID = args[0]
						kwargs.update({'contentID':contentID})
					except:
						raise KeyError('contentID')
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
								levr.log_error()
								raise TypeError('uid: '+ str(enc.encrypt_key(uid)))
							
						
					else:
						raise Exception('Invalid validation source')
					
					
					#check token validity
					#assure that the token was passed
					levr_token = self.request.get('levrToken')
					#check token against stored token
					if user:
						if levr_token == user.levr_token	: private = True
						else								: private = False
					else:
						private = False
					
					
					
					#compare the passed token to the db token
					#if token checks out, the private is True
					
					
				
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
					elif key == 'business':
						val = self.request.get('businessID')
						msg = 'businessID' + val
					#common mistakes. Youre welcome, debugger.
					elif key == 'uid'		: raise Exception('In validation declaration, "uid" should be "user".')
					elif key == 'dealID'	: raise Exception('In validation declaration, "dealID" should be "deal"')
					elif key == 'businessID': raise Exception('In validation declaration, "businessID" should be "business"')
					#default case
					else:
						val = self.request.get(key)
						msg = key+": "+val
					#requires is whether or not it is required
					required	= to_validate.get(key)
					#date_type pulls the type that the passed input should be
					try:
						data_type	= type_cast[key]
					except:
						levr.log_error('did not map type_cast dict correctly')
						raise Exception()
					#msg is passed to the exception handler if val fails validation
					
					logging.debug(msg)
					logging.debug(data_type)
					logging.debug(required)
					
					#handle case where input is not passed
					
					if 		not val and required				: raise KeyError(msg)
					elif 	not val and not required			: val = defaults[key]
					
					#handle case where input should be an integer
					elif data_type == int: 
						if val.isdigit():
							#convert to int
							val = int(val)
							
						else:
							levr.log_error()
							raise TypeError(msg)
					#handle case where input should be numerical 
					elif data_type == float:
						#float input
						try:
							#convert to float
							val = float(val)
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg)
					elif data_type == db.GeoPt:
						try:
							logging.debug(val)
							logging.debug(type(val))
							#convert to geopoint
							val = levr.geo_converter(val)
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
					elif data_type == levr.Business:
						try:
							val = db.Key(enc.decrypt_key(val))
							business = levr.Business.get(val)
							val = business
						except Exception,e:
							logging.error(e)
							raise TypeError(msg)
					elif data_type == list:
						try:
							#convert to list
							val = val.split(',')
						except Exception,e:
							logging.debug(e)
							raise TypeError(msg+"... must be a comma delimited string")
					elif data_type == bool:
						try:
							val = bool(val)
						except:
							logging.error(e)
							raise TypeError(msg)
					elif data_type == str:
						#nothing!
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
				send_error(self,'Server Error')
			else:
				return handler_method(self,*args,**kwargs)
		
		return validator
	
	return wrapper

def send_img(self,blob_key,size):
	try:
		logging.debug(levr.log_dir(blob_key.properties))
		
		logging.debug(str(blob_key.key()))
		
		
		#read the blob data into a string !!!! important !!!!
		blob_data = blob_key.open().read()
		
		logging.info('Blob size: '+str(blob_key.size))
		
		#pass blob data to the image handler
		img			= images.Image(blob_data)
		#get img dimensions
		img_width	= img.width
		img_height	= img.height
		logging.debug(img_width)
		logging.debug(img_height)
		
		logging.debug(img.get_original_metadata())
		logging.debug(levr.log_dict(img.get_original_metadata()))
		
		#define output parameters
		if size == 'large':
			#view for top of deal screen
			aspect_ratio 	= 2. 	#width/height
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
			aspect_ratio	= 1.5
			output_width	= 800.
		elif size == 'facebook':
			aspect_ratio 	= 1.
			output_width	= 250.
		elif size == 'emptySet':
			aspect_ratio	= 3.
			output_width	= 640.
		elif size == 'widget':
			aspect_ratio	= 1.
			output_width	= 150.
		elif size == 'webMapView':
			aspect_ratio	= 1.5
			output_width	= 400.
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
		output_img = img.execute_transforms(output_encoding=images.JPEG,quality=95)
		
		#write image to output
		self.response.headers['Content-Type'] = 'image/jpeg'
		self.response.out.write(output_img)
		logging.debug(str(self.response.headers))
		
	except KeyError,e:
		send_error(self,e)
	except Exception,e:
		levr.log_error()
		send_error(self,'Server Error')

def fetch_deals(keys,**kwargs):
	logging.debug('\n\n\n\t\t\t FETCH DEALS \n\n\n')
	#set namespace parameter
	development		= kwargs.get('development',False)
	if development	:namespace = levr.MEMCACHE_TEST_GEOHASH_NAMESPACE
	else			:namespace = levr.MEMCACHE_ACTIVE_GEOHASH_NAMESPACE
	logging.debug(namespace)
	
	
#def fetch_deals(deal_keys):
#	'''
#	Fetches deals from a list of deal keys
#	First tries memcache, and g
#	@param deal_keys:
#	@type deal_keys:
#	'''

def get_deal_keys(hash_set,**kwargs):
	'''
	<bullhorn> Why are we here?!
	<screams> To get deal keys!!
	<bullhorn> Why are we here?!
	<screams> To take what is ours!!
	<bullhorn> And how are we going to get it?!
	<screams> First we will search the memcache for all of the requested geohashes.
				The geohashes that are in the memcache will be returned with a list of deal_keys for that geohash
				The geohashes that are not in the memcache, we will perform a db query for that geohash and get
				the deal_keys that way. And then we will burn those motherfuckers to the ground!! Freeeeeeeedoooooooom!!!
				
	Returns: list of deal keys
	Optional kwargs:
		development = Boolean; if in development, will search for deal_text='test' otherwise deal_text='active'
	
	@param hash_set: the geohashes in question
	@type hash_set: list
	'''
	logging.debug('\n\n\n\t\t\t GET DEAL KEYS \n\n\n')
	development		= kwargs.get('development',False)
	if development:
		#developer is searching
		deal_status = 'test'
		namespace = levr.MEMCACHE_TEST_GEOHASH_NAMESPACE
		logging.debug('test deals')
	else:
		#a real person is searching!
		deal_status = 'active'
		namespace = levr.MEMCACHE_ACTIVE_GEOHASH_NAMESPACE
		logging.debug('active deals')
	
	# search hashes from memcache
	keys_dict, unresolved_hashes = get_from_memcache(hash_set,namespace)
	
	if unresolved_hashes:
		# search db for hashes, and place the results in the memcache
		more_keys = get_deal_keys_from_db(unresolved_hashes,deal_status,namespace)
		keys_dict.update(more_keys)
	
	# keys_dict is a dict mapping of hash:[key,]
	deal_keys = []
	count = 0
	for key in keys_dict:
		deal_keys.extend(keys_dict[key])
		count +=1
	logging.debug('total keys: '+str(count))
	return deal_keys
		
	

def get_from_memcache(mem_keys,namespace):
	'''
	Fetches a list of keys from the memcache with the given namespace
	Returns a dict of key:val from the memcache, 
		and a list of keys that were not resolved in the memcache
	@param mem_keys: list of memcache keys
	@type mem_keys: list
	@param namespace: 
	@type namespace: str
	'''
	
	logging.debug('\n\n\n\t\t\t GET FROM MEMCACHE \n\n\n')
	logging.debug(mem_keys)
	assert type(mem_keys) is list, 'mem_keys should be a list'
	
	#fetch deal_key lists by geohash
	key_dict = memcache.get_multi(mem_keys,namespace=namespace) #@UndefinedVariable
	
	#grab keys that were not successfully fetched from the memcache
	unresolved_keys = filter(lambda x: x not in key_dict,mem_keys)
	
	logging.debug('key_dict from memcache:')
	logging.debug(levr.log_dict(key_dict))
	logging.debug('unresolved_keys')
	logging.debug(unresolved_keys)
	return key_dict,unresolved_keys
	

def get_deal_keys_from_db(hash_set,deal_status,namespace):
	'''
	Returns a dict mapping of hashes and deal keys
	
	tags = list of tags that are strings
	request point is db.GeoPt format
	
	optional parameters:
	development		default=False
	
	'''
	logging.debug('\n\n\n\t\t\t GET FROM DB \n\n\n')
	####build search query
	hashes_and_keys = {}
	for query_hash in hash_set:
		#initialize query
		q = levr.Deal.all(keys_only=True).filter('deal_status',deal_status)
		
		#grab all deals in the geohash
		q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
		
		
		#FETCH DEAL KEYS
		fetched_deal_keys = q.fetch(None)
		logging.info('From: '+query_hash+", fetched: "+str(fetched_deal_keys.__len__()))
		
		# add deal keys to the dict that will be set to the memcache
		hashes_and_keys.update({query_hash:fetched_deal_keys})
		
		
	# add keys to memcache
	logging.debug('keys from db')
	logging.debug(levr.log_dict(hashes_and_keys))
	set_deal_keys_to_memcache(hashes_and_keys,namespace)
	
	return hashes_and_keys

def set_deal_keys_to_memcache(hashes_and_keys,namespace):
	'''
	Takes a mapping of {hash:deal_keys} and adds them to memcache as {key=hash:val=deal_keys}
	@param hashes_and_keys: {geohash:[deal.key(),]}
	@type hashes_and_keys: dict
	'''
	logging.debug('\n\n\n\t\t\t SET TO MEMCACHE \n\n\n')
	failsafe = 0
	# tries to set the hashes to memcache a max of 5 times
	while True and failsafe <5:
		failsafe +=1
		#set_multi returns a 
		rejected_keys = memcache.set_multi(hashes_and_keys,namespace=namespace) #@UndefinedVariable
		logging.debug('rejected keys: '+str(rejected_keys))
		if rejected_keys:
			#some of the keys were not updated properly
			hashes_and_keys = {hash:hashes_and_keys[ghash] for ghash in rejected_keys }
		else:
			#nothing was rejected, break loop
			break

	logging.debug('set_deal_keys_to_memcache iterations: {}'.format(failsafe))
	return


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
Earth_radius_mi = 3958.76
RADIUS = Earth_radius_mi
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
	
	logging.debug('Karma: '+str(user.karma))
	logging.debug('Level: '+str(user.level))
	
	if new_level != old_level:
		#level up notification
		levr.create_notification('levelup',user.key(),user.key(),new_level=new_level)
		logging.debug('New level: '+str(user.level+1))
		
	user.level = new_level
		
	return user

def merge_customer_info_from_B_into_A(user,donor,service):
	'''
	Merges the donor into the user. Donor can only pass info from one social service at a time.
	If the donor is connected to more than one social service, you must call this function for each service
	
	@param user: the user getting the properties, i.e. the base user
	@type user: Customer
	@param donor: The old user that is being deprecated
	@type donor: Customer
	@param service: the social service that is being connected (which is why the properties need to be translated)
	@type service: foursquare, facebook, twitter <str>
	
	Returns the altered user and donor entities THAT HAVE BEEN PUT
	'''
	#===================================================================
	# Merge user data from donor to user
	#===================================================================
	
	if donor.tester or user.tester: user.tester = True
	user.karma += donor.karma
	levr.level_check(user)
	
	user.new_notifications += donor.new_notifications
	#===================================================================
	# Notification references - dont care about actor references
	#===================================================================
	notification_references = levr.Notification.all().filter('to_be_notified',donor.key()).fetch(None)
	for n in notification_references:
		n.to_be_notified.remove(donor.key())
	db.put(notification_references)
	
	#===================================================================
	# remove all follower references to the donor - these will be reset with remote api call
	#===================================================================
	donor_references = levr.Customer.all().filter('followers',donor.key()).fetch(None)
	for u in donor_references:
		u.followers.remove(donor.key())
	db.put(donor_references)
	
	#===================================================================
	# Point back to the new owner for the sake of that user getting the right upvotes
	#===================================================================
	donor.email = 'dummy@levr.com'
	donor.pw = str(user.key())
	
	if service == 'foursquare':
		logging.info('The user came from foursquare')
		user = social.Foursquare(user,'verbose')
		#connect the user using foursquare
		new_user, new_user_details, new_friends = user.first_time_connect(
								foursquare_token=donor.foursquare_token
								)
		# Wipe donors identifying information
		donor.foursquare_connected = False
		donor.foursquare_id = -1
		donor.foursquare_token = ''
		donor.foursquare_friends = []
	elif service == 'facebook':
		logging.info('The user came from facebook')
		user = social.Facebook(user,'verbose')
		#connect the user using facebook
		new_user, new_user_details, new_friends = user.first_time_connect(
								facebook_token=donor.facebook_token
								)
		donor.facebook_connected = False
		donor.facebook_id = -1
		donor.facebook_token = ''
		donor.facebook_friends = []
	elif service == 'twitter':
		logging.info('The user came from twitter')
		user = social.Twitter(user,'verbose')
		#connect the user using facebook
		new_user, new_user_details, new_friends = user.first_time_connect(
								twitter_token=donor.twitter_token
								)
		donor.twitter_connected = False
		donor.twitter_token = ''
		donor.twitter_token_secret = ''
		donor.twitter_id = -1
		donor.twitter_screen_name = ''
		donor.twitter_friends_by_id = []
		donor.twitter_friends_by_sn = []
	else:
		raise Exception('social service not recognized: '+service)
	logging.debug('New friends:, New details:')
	logging.debug(new_friends)
	logging.debug(new_user_details)
	donor.put()
	return new_user, donor
def search_foursquare(geo_point,token,deal_status,already_found=[],**kwargs):
	assert deal_status != 'random', 'Deal status is being set as random'
	#if token is passes as 'random', use a hardcoded token
	if token == 'random':
		hardcoded = ['IDMTODCAKR34GOI5MSLEQ1IWDJA5SYU0PGHT4F5CAIMPR4CR','ML4L1LW3SO0SKUXLKWMMBTSOWIUZ34NOTWTWRW41D0ANDBAX','RGTMFLSGVHNMZMYKSMW4HYFNEE0ZRA5PTD4NJE34RHUOQ5LZ']
		token = random.choice(hardcoded)
	logging.info('Using token: '+token)
	
	
	url = 'https://api.foursquare.com/v2/specials/search?v=20120920&ll='+str(geo_point)+'&limit=50&oauth_token='+token
	result = urlfetch.fetch(url=url)
	if result.status_code != 200:
		# Foursquare request was not successful
		logging.debug(result.content)
		levr.log_error(result.headers.data)
		return
	
	result = json.loads(result.content)
	foursquare_deals = result['response']['specials']['items']
	logging.debug(foursquare_deals)
	
	#initialize return array
	response_deals = []
	
	for foursquare_deal in foursquare_deals:
#		logging.info('woo a deal!')
		
#		logging.debug(foursquare_deal)
#		logging.debug(foursquare_deal['venue'])
#		logging.debug(levr.log_dict(foursquare_deal))
#		logging.debug(levr.log_dict(foursquare_deal['venue']))
		
		#sometimes venues do not have categories
		if len(foursquare_deal['venue']['categories']) == 0:
			logging.info('No venue category returned, making it "undefined"')
			foursquare_deal['venue']['categories'] = [{'name':'undefined'}]
		#logging.info(foursquare_deal['venue'])
		if not filter_foursquare_deal(foursquare_deal,already_found):
			venue = foursquare_deal['venue']
			#logging.debug(foursquare_deal['type'])
			#logging.debug(foursquare_deal['message'])
			#logging.debug(foursquare_deal['venue']['categories'][0]['name'])
			#logging.info(foursquare_deal['id'])
			#does business already exist?
			existing_business = levr.Business.gql('WHERE foursquare_id=:1',foursquare_deal['venue']['id']).get()
			
			#### DEBUG
			bs = levr.Business.all().filter('foursquare_id',foursquare_deal['venue']['id']).count()
			if bs >1: levr.log_error('Multiple businesses have the same foursquare_id: '+ repr(foursquare_deal['venue']['id']))
			
			#### /DEBUG
			
			if not existing_business:
				logging.debug('business does not exist, foursquare_id: '+repr(foursquare_deal['venue']['id'])+' business_name: '+repr(venue['name']))
				
				business = levr.Business(
					business_name 		=	venue['name'],
					foursquare_name		=	venue['name'],
					foursquare_id		=	venue['id'],
					foursquare_linked	=	True,
					vicinity			=	venue['location']['address'] + ', ' + venue['location']['city'],
					geo_point			=	db.GeoPt(venue['location']['lat'],venue['location']['lng']),
					geo_hash			=	geohash.encode(venue['location']['lat'],venue['location']['lng']),
					types				=	[venue['categories'][0]['name']]
				)
				business.put()
				#logging.debug(business.__dict__)
			else:
				logging.info('business already exists:')
				logging.debug(levr.log_model_props(existing_business,['geo_point','business_name','vicinity','geo_hash']))
				business = existing_business
			
			
			#does deal already exist?
			existing_deal = levr.Deal.all().filter('foursquare_id',foursquare_deal['id']
											).filter('businessID',str(business.key())
											).filter('deal_status',deal_status
											).get()
#			existing_deal = levr.Deal.gql('WHERE foursquare_id=:1',foursquare_deal['id']).get()
			logging.warning(foursquare_deal['id'])
			if not existing_deal:
				
				#add the foursquare deal
				deal = add_foursquare_deal(foursquare_deal,business,deal_status)
			
			else:
				deal = existing_deal
				logging.info('Foursquare special '+deal.foursquare_id+' found in database but not in search.')
#				logging.debug('foursquare')
				#logging.debug(levr.log_model_props(deal))
			deal_business = db.get(deal.businessID)
			#calculate distance
			distance = distance_between_points(geo_point.lat, geo_point.lon, deal_business.geo_point.lat, deal_business.geo_point.lon)
			#calculate distance
			distance2 = distance_between_points(geo_point.lat, geo_point.lon, business.geo_point.lat, business.geo_point.lon)

# 			logging.debug('DISTANCE!!!: '+str(distance))
			logging.debug('distance: '+str(distance)+ ' or '+ str(distance2))
			logging.warning('geopoint1: '+str(deal_business.geo_point)+', geopoint2: '+ str(business.geo_point))
			if distance < 10:
				#package deal
				packaged_deal = package_deal(deal,distance=distance)
				response_deals.append(packaged_deal)
			else:
				pass
#				logging.debug('Deal not added because it was too far away: '+str(distance)+' miles')
			
		#end valid deal level
	#end for loop
#	
#	for deal in response_deals:
#		logging.info(deal['dealText'])
	return response_deals

def add_foursquare_deal(foursquare_deal,business,deal_status):
	#grab a random ninja to be the owner of this deal
	random_dead_ninja = get_random_dead_ninja()
	
	
	#silly multiline strings in foursquare api
	message = foursquare_deal['message']
	if message.find('\r\n') != -1:
		message = message[0:message.find('\r\n')]
	elif message.find('\r') != -1:
		message = message[0:message.find('\r')]
	elif message.find('\n') != -1:
		message = message[0:message.find('\n')]
	else:
		#logging.debug('NO FUCKERY IN THIS HERE STRING')
		pass
	
	logging.debug('\n\n\t\t\t foursquare deal info \n\n')
	logging.debug(foursquare_deal['message']+' '+foursquare_deal['description']+' '+foursquare_deal['venue']['name']+' '+foursquare_deal['venue']['categories'][0]['name'])
	##logging.debug(json.dumps(foursquare_deal['message'].rstrip('\r\n')))
	
	
	
	
	
	#===========================================================================
	# Create deal
	#===========================================================================
	#build tags
	tags = levr.tagger(foursquare_deal['message']+' '+foursquare_deal['venue']['name']+' '+foursquare_deal['venue']['categories'][0]['name'])
	logging.debug(tags)
	logging.debug(type(tags))
	#Do not include these tags: +' '+foursquare_deal['description']
	
	
	deal = levr.Deal(
		businessID		=	str(business.key()),
		business_name	=	foursquare_deal['venue']['name'],
		deal_status		=	deal_status,
		tags			=	tags,
		origin			=	'foursquare',
		external_url	=	'foursquare://venues/'+foursquare_deal['venue']['id'],
		foursquare_id	=	foursquare_deal['id'],
		foursquare_type	=	foursquare_deal['venue']['categories'][0]['name'],
		deal_text		=	message,
		description		=	message,
		geo_point		=	business.geo_point,
		geo_hash		=	business.geo_hash,
		pin_color		=	'blue',
		parent			=	random_dead_ninja.key(),
		smallImg		=	'http://playfoursquare.s3.amazonaws.com/press/logo/icon-512x512.png'
	)
	try:
		deal.business = business
	except:
		levr.log_error()


	deal.put()
	
	#===========================================================================
	# Update memcache because a deal was created
	#===========================================================================
	if deal.deal_status == 'active':
		namespace = levr.MEMCACHE_ACTIVE_GEOHASH_NAMESPACE
	elif deal.deal_status == 'test':
		namespace = levr.MEMCACHE_TEST_GEOHASH_NAMESPACE
	else:
		raise Exception('Invalid memcahce namespace')
	levr.update_deal_key_memcache(deal.geo_point,deal.key(),namespace)
	
	logging.info('Foursquare special '+deal.foursquare_id+' added to database.')
	#logging.debug(levr.log_model_props(deal))
	
	return deal


def filter_foursquare_deal(foursquare_deal,already_found):
	
# 	allowed_categories = ["Afghan Restaurant", "African Restaurant", "American Restaurant", "Arepa Restaurant", "Argentinian Restaurant", "Asian Restaurant", "Australian Restaurant", "BBQ Joint", "Bagel Shop", "Bakery", "Brazilian Restaurant", "Breakfast Spot", "Brewery", "Burger Joint", "Burrito Place", "Caf\u00e9", "Cajun / Creole Restaurant", "Caribbean Restaurant", "Chinese Restaurant", "Coffee Shop", "Cuban Restaurant", "Cupcake Shop", "Deli / Bodega", "Dessert Shop", "Dim Sum Restaurant", "Diner", "Distillery", "Donut Shop", "Dumpling Restaurant", "Eastern European Restaurant", "Ethiopian Restaurant", "Falafel Restaurant", "Fast Food Restaurant", "Filipino Restaurant", "Fish & Chips Shop", "Food Truck", "French Restaurant", "Fried Chicken Joint", "Gastropub", "German Restaurant", "Gluten-free Restaurant", "Greek Restaurant", "Hot Dog Joint", "Ice Cream Shop", "Indian Restaurant", "Indonesian Restaurant", "Italian Restaurant", "Japanese Restaurant", "Juice Bar", "Korean Restaurant", "Latin American Restaurant", "Mac & Cheese Joint", "Malaysian Restaurant", "Mediterranean Restaurant", "Mexican Restaurant", "Middle Eastern Restaurant", "Molecular Gastronomy Restaurant", "Mongolian Restaurant", "Moroccan Restaurant", "New American Restaurant", "Peruvian Restaurant", "Pizza Place", "Portuguese Restaurant", "Ramen / Noodle House", "Restaurant", "Salad Place", "Sandwich Place", "Scandinavian Restaurant", "Seafood Restaurant", "Snack Place", "Soup Place", "South American Restaurant", "Southern / Soul Food Restaurant", "Spanish Restaurant", "Steakhouse", "Sushi Restaurant", "Swiss Restaurant", "Taco Place", "Tapas Restaurant", "Tea Room", "Thai Restaurant", "Turkish Restaurant", "Vegetarian / Vegan Restaurant", "Vietnamese Restaurant", "Winery", "Wings Joint", "Bar", "Beer Garden", "Cocktail Bar", "Dive Bar", "Gay Bar", "Hookah Bar", "Hotel Bar", "Karaoke Bar", "Lounge", "Nightclub", "Other Nightlife", "Pub", "Sake Bar", "Speakeasy", "Sports Bar", "Strip Club", "Whisky Bar", "Wine Bar"]
	
	
#	logging.info('---------------------------------------------')
#	logging.info('Type: '+foursquare_deal['type'])
#	logging.info('Message: '+foursquare_deal['message'])
#	logging.info('Description: '+foursquare_deal['description'])
#	logging.info('Category: '+foursquare_deal['venue']['categories'][0]['name'])
	
	allowed_types = ['count','regular','flash','swarm','other','frequency']	#not mayor
	
# 	logging.debug(foursquare_deal['venue']['categories'])
	
# 	if foursquare_deal['venue']['categories'][0]['name'] not in allowed_categories:
# 		pass
		#logging.info('Special '+foursquare_deal['id']+' filtered out because it was from a non-allowed category: '+foursquare_deal['venue']['categories'][0]['name'])
#		return True
#		logging.info('Special from category: '+foursquare_deal['venue']['categories'][0]['name']+' allowed because category filter is turned off')
	if foursquare_deal['type'] not in allowed_types:
		logging.info('Special '+foursquare_deal['id']+' filtered out because it was of a non-allowed type: '+foursquare_deal['type'])
		return True
	elif foursquare_deal['id'] in already_found:
		logging.info('Special '+foursquare_deal['id']+' filtered out because it was already found in the database.')
		return True
		
	#search keywords to weed out more deals
	types = ['mayor','w/coupon! Text','spg.com/better','topguest.com','www.','gift card','disney on ice']
	for dealType in types:
		if dealType in foursquare_deal['message'] or dealType in foursquare_deal['description']:
			logging.info('Special '+foursquare_deal['id']+' filtered out because the non-allowed keyword "'+dealType+'" was found in the message or description.')
			return True
			
	#search description strings to weed out deals that require more than 1 checkin in a given number of days
	allowed_description_fragments = ['Unlocked every check-in','1st check-in','Unlocked for checking in 1 times','Unlocked for swarms','consecutive','chance to win']
	
	
	flag='notfound'
	for fragment in allowed_description_fragments:
		if fragment in foursquare_deal['description']:
			flag='found'
	if flag == 'notfound':
		logging.info('Special '+foursquare_deal['id']+' filtered out because a non-allowed description was found: '+foursquare_deal['description'])
		return True
		
		
	#if everything passes okay, return the falsities!
	return False
		
def get_random_dead_ninja(sample_size=1):
	#get keys of all the dead ninjas
	dead_ninjas		= levr.Customer.all(keys_only=True).filter('email',levr.UNDEAD_NINJA_EMAIL).fetch(None)
#	dead_ninjas		= levr.Customer.all(keys_only=True).filter('email','deadninja@levr.com').fetch(None)
	
	assert dead_ninjas, 'There are no undead ninjas in the database'
	
	#select a random dead ninja
	dead_ninja_key	= random.sample(dead_ninjas,int(sample_size))
	#fetch the dead ninja entity
	dead_ninja		= db.get(dead_ninja_key)
	
	
	if sample_size == 1:
		dead_ninja = dead_ninja[0]
	
	#<chief ninja>: Good luck - you're doing your country a great service.
	#<crowd>: "one of us! one of us! one of us!"
	#<dead ninja> "well ah well okay i guess, but you see right now isn't a terribly good time for me, you see, it's just that I have this very important appointment..." [drowned out by]
	#<crowd>: "one of us! one of us! one of us! one of us!" [dead ninja is pushed towards the door] "one of us! one of us! one of us!"
	#<dead ninja> [To himself] "I never could get the hang of Thursdays..."
	return dead_ninja
	
def match_foursquare_business(geo_point,query):
	
	params = {
		'client_id'		: 	'UNHLIF5EYXSKLX50DASZ2PQBGE2HDOIK5GXBWCIRC55NMQ4C',
		'client_secret' : 	'VLKDNIT0XSA5FK3XIO05DAWVDVOXTSUHPE4H4WOHNIZV14G3',
		'v'				:	'20120920',
		'intent'		:	'match',
		'll'			:	str(geo_point),
		'query'			:	query
	}
	
	#geocode the vicinity because we don't trust the geoPoint coming back from google (sometimes misleading)
	# geo_url = 'https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address='+vicinity
# 	
# 	result = urlfetch.fetch(url=geo_url)
# 	result = json.loads(result.content)
# 	
# 	logging.debug(result)
	
	#url = 'https://api.foursquare.com/v2/venues/search?'+urllib.urlencode(params)
	
	url = 'https://api.foursquare.com/v2/venues/search?v='+params['v']+'&intent='+params['intent']+'&ll='+params['ll']+'&query='+urllib.quote(params['query'])+'&client_id='+params['client_id']+'&client_secret='+params['client_secret']
	
	#url = 'https://api.foursquare.com/v2/venues/search?v=20120920&intent=match&ll='+str(geo_point)+'&query='+query+'&client_id='+client_id+'&client_secret='+client_secret
	
	logging.debug(url)
	
	
	result = urlfetch.fetch(url=url)
	result = json.loads(result.content)
	
	venues = result['response']['venues']
	
	logging.debug(result)
	
	logging.debug(levr.log_dict(venues[0]))
	
	if venues:
		match = venues[0]
		logging.info('Matching Foursquare businesses found. Mapping "'+query+'" to "'+match['name']+'".')
		
		response = {
			'foursquare_name'		:	match['name'],
			'foursquare_id'		:	match['id']
		}
		
		return response
	else:
		return False
		
def update_foursquare_business(foursquare_id,deal_status,token='random'):

	logging.info('''
						
			Updating the deals at the following business:
							
	''')
	logging.info(foursquare_id)


	#if token is passes as 'random', use a hardcoded token
	if token == 'random':
		hardcoded = ['IDMTODCAKR34GOI5MSLEQ1IWDJA5SYU0PGHT4F5CAIMPR4CR','ML4L1LW3SO0SKUXLKWMMBTSOWIUZ34NOTWTWRW41D0ANDBAX','RGTMFLSGVHNMZMYKSMW4HYFNEE0ZRA5PTD4NJE34RHUOQ5LZ']
		token = random.choice(hardcoded)
		logging.info('Using token: '+token)
	

	#go grab the business from foursquare
	params = {
		'v'				:	'20120920',
		'oauth_token'	:	token
	}

	url = 'https://api.foursquare.com/v2/venues/'+foursquare_id+'?'+urllib.urlencode(params)
	
	result = urlfetch.fetch(url=url)
	result = json.loads(result.content)
	#logging.info(result)
	foursquare_deals = result['response']['venue']['specials']['items']

	#push dealids onto an array
	foursquare_deal_ids = []
	for special in foursquare_deals:
		foursquare_deal_ids.append(special['id'])
	logging.info(foursquare_deal_ids)
	
	#grab the business with that foursquare id
	business = levr.Business.gql('WHERE foursquare_id = :1',foursquare_id).get()
	business_key = business.key()
	#grab the deals from that business
	#deals = levr.Deal.gql('WHERE businessID = :1',str(business_key))
	deals = levr.Deal.gql('WHERE businessID = :1 AND origin = :2 AND deal_status = :3',str(business_key),'foursquare',deal_status)
	
	for deal in deals:
		
		if deal.foursquare_id not in foursquare_deal_ids:
			#remove levr-stored foursquare deals not returned by the foursquare venue request (foursquare has removed them)
			deal.deal_status = 'expired'
			logging.info('The foursquare special '+deal.foursquare_id+' has been retired because it was not found on the foursquare servers.')
			#put back
			deal.put()
		else:
			#levr-stored deal WAS found in foursquare list, so remove from the list
			#list comprehension should remove the foursquare_deal_id AND handle duplicates
			foursquare_deal_ids = [x for x in foursquare_deal_ids if x != deal.foursquare_id]
			logging.info('matched deal!')
			logging.info(foursquare_deal_ids)
	
	
	
	#anything left in the list?
	if len(foursquare_deal_ids) > 0:
		logging.info('THERE IS SOMETHING IN THE LIST')	
		#add any extra deals
		for foursquare_deal in foursquare_deals:
			if foursquare_deal['id'] in foursquare_deal_ids:
				#check the deal against the filter function
				already_found = []
				#rearrange the deal
				foursquare_deal.update({
					'venue'		:	result['response']['venue']
				})
				# logging.info('THE DEAL:')
# 				logging.info(levr.log_dict(foursquare_deal))
				if not filter_foursquare_deal(foursquare_deal,already_found):
					#sometimes there isn't a category
					if len(foursquare_deal['venue']['categories']) == 0:
						logging.info('No venue category returned, making it "undefined"')
						foursquare_deal['venue']['categories'] = [{'name':'undefined'}]
					
					#add the deal
					deal = add_foursquare_deal(foursquare_deal,business,deal_status)
# 	
# 	#go grab all the deals from that business
# 	deals = levr.Deal.gql('WHERE foursquare_id = :1',foursquare_id)
# 	
# 	for deal in deals:
# 		logging.info(deal.foursquare_id)
# 		logging.info('deal found!')
# 	
# 	
	
	#pull the specials
	#logging.info(foursquare_deals)



	
#delete account and all follower references
class PromoteDeal:
	'''
	Class for promoting deals. Mostly for namespacing.
	'''
	def __init__(self,deal):
		self.deal = deal
	def put(self):
		self.deal.put()
		return self.deal
	def increase_karma(self,**kwargs):
		'''
		Gives the deal preference over other deals so that it is shown before them
		This is done by adding karma to the deal without increasing the upvotes
		'''
		self.deal.karma += 200
		
		if kwargs.get('auto_put',True) == True:
			self.deal.put()
			return self.deal
		else:
			return self
	def add_tags(self,tags,**kwargs):
		'''
		Increases the tags on a deal so that it is more visible
		
		@param tags: a list of tags
		@type tags: list
		'''
		assert type(tags) == list, 'tags must be a list'
		
		self.deal.tags.extend(tags)
		
		if kwargs.get('auto_put',True) == True:
			self.deal.put()
			return self.deal
		else:
			return self
	


class SpoofUndeadNinjaActivity:
	'''
	The undead walk the earth! And they like things!
	Takes a user, calculates the time since their last login, and creates a number of 
	notifications with a probability based on values we specify.
	
	variables:
	max_likes_per_day
	ideal_likes_per_day
	'''
	def __init__(self,user,development=False,**kwargs):
		self.user = user
		self.development = development
		self.now = datetime.now()
		self.now_in_seconds = long(levr.unix_time(self.now))
		logging.info(levr.log_model_props(self.user,['first_name','display_name']))
		#fetch all of the users active deals
		self.user_deals	= levr.Deal.all().ancestor(self.user.key()).fetch(None)
		logging.debug(self.user_deals)
		#calculate the date since last upload
		logging.debug(self.user.date_last_login)
#		logging.debug(type(self.user.date_last_login))
		self.days_since_last_login = self.calc_days_since(self.user.date_last_login)
		logging.debug(self.days_since_last_login)
#		logging.debug(type(self.days_since_last_login))
		
		#set environment params
		self.max_likes_per_day		= kwargs.get('max_likes_per_day',3) #a.k.a. the number of chances to like in a day
		
		self.ideal_likes_per_day	= float(kwargs.get('ideal_likes_per_day',2))
		
		#constrain system...
		assert type(self.max_likes_per_day) == int, 'max likes per day must be int'
		assert type(self.ideal_likes_per_day) == float or type(self.ideal_likes_per_day) == int , 'ideal_likes_per_day must be float or int'
		assert self.max_likes_per_day > self.ideal_likes_per_day , 'Max likes per day must be greater than the ideal'
		
		#set the chance that the deal will be liked per iteration
		self.chance_of_like = self.ideal_likes_per_day / self.max_likes_per_day
		
		
	def run(self):
		'''
		WARNING: DOES NOT REPLACE THE USER WHEN RETURNING
		'''
		#the users accumulated notifications
		notifications = []
		#the accumulated undead ninjas
		undead_ninjas_set = set()
		for deal in self.user_deals:
#			days_since_upload = self.calc_days_since(deal.date_created)
#			logging.debug(days_since_upload)
			whole_days = int(floor(self.days_since_last_login))
			partial_days = self.days_since_last_login - whole_days
			
			#add up likes for whole days
			total_likes = 0
			for day in range(0,whole_days): #@UnusedVariable
				total_likes += self.get_likes_per_day(self.chance_of_like, self.max_likes_per_day)
			
			#add up likes from the partial day
			total_likes += self.get_likes_per_day(self.chance_of_like, self.max_likes_per_day) * partial_days
			
			
#			likes_per_day	= self.get_likes_per_day(self.chance_of_like, self.max_likes_per_day)
#			logging.debug('likes per day: '+str(likes_per_day))
#			logging.debug('total days: '+str(self.days_since_last_login))
#			total_likes		= likes_per_day * self.days_since_last_login
			logging.debug('total likes: '+str(total_likes))
			#round off total likes to an integer
			total_likes		= floor(total_likes)
			logging.debug('total likes: '+str(total_likes))
			
			
			#fetch the appropriate number of ninjas
			undead_ninjas = get_random_dead_ninja(total_likes)
			logging.debug(undead_ninjas)
			#make sure undead_ninjas is a list
			if type(undead_ninjas) != list:
				undead_ninjas = [undead_ninjas]
			#add these undead ninjas to the list of undead ninjas that are being updated
			
			
			#The decided number of ninjas will like the deal
			for ninja in undead_ninjas:
				#only add the 
				if deal.key() not in ninja.upvotes:
					#increase the deals upvotes
					deal.upvotes += 1
					#log that the undead ninja has liked this deal
					ninja.upvotes.append(deal.key())
					#increase the users karma
					self.user.karma += 1
					#update notification count
					self.user.new_notifications += 1
					#===========================================================
					# Remember to change this if the create notifications functionality changed
					#===========================================================
					#create the notification
					notifications.append(levr.Notification(
										notification_type	= 'favorite',
										line2				= random.choice(levr.upvote_phrases),
										to_be_notified		= [self.user.key()],
										actor				= ninja.key(),
										deal				= deal.key(), #default to None,
										date_in_seconds		= self.now_in_seconds
										))
					logging.debug('New notification')
				else:
					pass
			undead_ninjas_set.update(undead_ninjas)
					
					
		
		#update the users level
		levr.level_check(self.user)
		
		db.put(notifications)
#		db.put(self.user)
		db.put(undead_ninjas_set)
		
		return {
			'notifications':str(notifications),
			'user':self.user,
			'undead_ninjas':str(undead_ninjas_set)
			}
	def get_likes_per_day(self,chance_to_like,max_likes):
		'''
		Generates the number of likes per day the deal will get based on the chance that the deal will be liked in a day and the max number of likes in a day
		
		@param chance_to_like: The chance that the deal will be liked per simulation
		@type chance_to_like: float 0-1
		@param max_likes: The number of times the simulation will be run
		@type max_likes: int
		'''
		likes = 0
		for i in range(0,max_likes): #@UnusedVariable
			num = random.uniform(0,1)
			if num <= chance_to_like:
				likes += 1
		return likes
		
		
	
	
	def calc_days_since(self,date):
		diff = self.now - date
		logging.debug(self.now)
		logging.debug(date)
		logging.debug(type(date))
		logging.debug(diff)
		logging.debug(type(diff))
		logging.debug(diff.total_seconds)
		seconds_since = self.now_in_seconds - levr.unix_time(date)
		logging.debug(seconds_since)
		days_since = seconds_since/60./60./24.
		logging.debug('days since: '+str(days_since))
		return days_since
		
		
		
		
		
