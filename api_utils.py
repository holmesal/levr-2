import json
import levr_encrypt as enc
import levr_classes as levr
import logging
import os
import geo.geohash as geohash
from datetime import datetime

from google.appengine.ext import db
from google.appengine.api import images
from math import sin, cos, asin, sqrt, degrees, radians


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

def package_deal(deal,private=False):
#	logging.debug(str(deal.geo_point))
	packaged_deal = {
			'barcodeImg'	: deal.barcode,
			'business'		: package_business(levr.Business.get(deal.businessID)),
			'dateUploaded'	: str(deal.date_end)[:19],
			'dealID'		: enc.encrypt_key(deal.key()),
			'dealText'		: deal.deal_text,
			'description'	: deal.description,
			'isExclusive'	: deal.is_exclusive,
			'largeImg'		: create_img_url(deal,'large'),
			'geoHash'		: deal.geo_hash,
			'geoPoint'		: str(deal.geo_point),
			'redemptions'	: deal.count_redeemed,
			'smallImg'		: create_img_url(deal,'small'),
			'status'		: deal.deal_status,
			'shareURL'		: create_share_url(deal),
			'tags'			: deal.tags,
			'dateEnd'		: str(deal.date_end)[:19]
			}
	if private == True:
		packaged_deal.update({
							})
		
	return packaged_deal
def package_user(user,private=False,followers=True,**kwargs):
	'''alias is added by us, first_name and last_name should be added by all other services (foursquare for sure right now)'''
	if user.alias != '':
		alias  = user.alias
	else:
		alias = 'Clint Eastwood'
	
	packaged_user = {
		'uid'			: enc.encrypt_key(str(user.key())),
		'alias'			: alias,
		'dateCreated'	: user.date_created.__str__()[:19],
		'firstName'		: user.first_name,
		'lastName'		: user.last_name,
		'photo'			: user.photo,
		}
	if followers == True:
		followers_list = levr.Customer.get(user.followers)
		packaged_user['followers'] = [package_user(f,True,False) for f in followers_list]
	
	#check if the token will be sent with the response
	send_token = kwargs.get('send_token')
	if send_token:
		packaged_user.update({
							'levr_token': user.levr_token
							})
	
	if private:
		packaged_user.update({
							'moneyAvailable'	: 1,
							'moneyEarned'		: 1,
							})
	
	return packaged_user
def package_notification(notification):
	packaged_notification = {
		'notificationID'	: enc.encrypt_key(str(notification.key())),
#		'date'				: str(notification.date)[:19],
		'date'				: notification.date_in_seconds,
		'notificationType'	: notification.notification_type,
		'user'				: package_user(notification.actor),
		'notificationID'	: enc.encrypt_key(notification.key())
		}
	if notification.deal:
		packaged_notification['deal'] = package_deal(notification.deal)
	
	return packaged_notification
	
def package_business(business):
	packaged_business = {
		'businessID'	: enc.encrypt_key(str(business.key())),
		'businessName'	: business.business_name,
		'vicinity'		: business.vicinity,
		'owner'			: business.owner,
		'foursquareID'	: business.foursquare_id,
		'foursquareName': business.foursquare_name,
		'geoPoint'		: str(business.geo_point),
		'geoHash'		: business.geo_hash
						}
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
	
	
def get_deals_in_area(tags,request_point,radius=2,limit=None,precision=5,verbose=False):
	'''
	tags = list of tags that are strings
	request point is db.GeoPt format
	radius is miles
	'''
	
	#hash the reuqested geo_point
	center_hash = geohash.encode(request_point.lat,request_point.lon,precision=precision)
	logging.debug(center_hash)
	
	#get the hashes of the center geo_point and the 8 surrounding hashes
	hash_set = geohash.expand(center_hash)
	logging.debug(hash_set)
	
	t0 = datetime.now()
	#################DEBUG
#	ref_query = levr.Deal.all().filter('deal_status =','active')
#	for tag in tags:
#		if tag != 'all':
#			ref_query.filter('tags =',tag)
#	ref_deals = ref_query.fetch(None)
#	logging.info("total number of deals: "+str(ref_deals.__len__()))
#	for d in ref_deals:
#		logging.debug(d.geo_hash)
	##################/DEBUG
	
	t1 = datetime.now()
	SPECIAL_QUERIES = ['all','popular','new','hot']
	####build search query
	#only grabbing deal keys, then batch get array
	deal_keys = []
	for query_hash in hash_set:
		#only grab keys for deals that have active status
		q = levr.Deal.all(keys_only=True).filter('deal_status =','active')
		
		logging.debug('FLAG')
		logging.debug("tags: "+str(tags))
		#FILTER BY TAG
		#do not filter by tags if the tag is one of the special key words
		if tags and tags[0] not in SPECIAL_QUERIES:
			#grab all deals where primary_cat is in tags
			for tag in tags:
				logging.debug('tag: '+str(tag))
				q.filter('tags =',tag)
		else:
			logging.debug('This is a special case. Not filtering by tags: '+str(tags))
		
		
		#FILTER BY GEOHASH
		q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
#					logging.debug(q)
#					logging.debug(levr.log_dict(q.__dict__))
		
		
		#FETCH DEAL KEYS
		fetched_deals = q.fetch(None)
		logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
		
		deal_keys.extend(fetched_deals)
#					logging.debug(deal_keys)
	t2 = datetime.now()
	
	#BATCH GET RESULTS
	deals = levr.Deal.get(deal_keys)
	
	t3 = datetime.now()
	
	#FILTER THE DEALS BY DISTANCE
	filtered_deals = filter_deals_by_radius(deals,request_point,radius)
	
	logging.debug(limit)
	#LIMIT DEALS
	if limit:
		logging.debug('flag')
	else:
		logging.debug('unflag')
	logging.debug(filtered_deals.__len__())
	logging.debug(filtered_deals.__len__() >= int(limit))
	
	
	if limit and filtered_deals.__len__() >= int(limit):
		logging.debug('FLAG LIMITED')
		filtered_deals = filtered_deals[:int(limit)]
	else:
		logging.debug('FLAG UNLIMITED')
	
	t4 = datetime.now()
	
	
	####################### DEBUG
	logging.debug('Start')
	logging.debug(deals.__len__())
	logging.debug(filtered_deals.__len__())
	logging.debug('End')
	
	fetch_time = t2-t1
	get_time = t3-t2
	filter_time = t4-t3
	unfiltered_count = deals.__len__()
	filtered_count = filtered_deals.__len__()
	if verbose == True:
		return (filtered_deals,fetch_time,get_time,filter_time,unfiltered_count,filtered_count)
	else:
	######################### /DEBUG
	
	
	
		return filtered_deals

def filter_deals_by_radius(deals,center,radius):
	'''
	http://stackoverflow.com/questions/3182260/python-geocode-filtering-by-distance
	'''
	logging.debug('FILTER BY RADIUS')
	#Only returns deals that are within a radius of the center
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
		












