#from common_word_list import blacklist
from datetime import datetime, timedelta
from google.appengine.api import files, images, urlfetch, memcache, taskqueue
from google.appengine.ext import blobstore, db, ndb
from math import sin, cos, asin, degrees, radians, floor, sqrt
import api_utils_social as social
import geo.geohash as geohash
import json
import levr_classes as levr
import levr_encrypt as enc
import logging
import os
import promotions as promo
import random
import urllib
import webapp2
#from tasks import INCREMENT_DEAL_VIEW_URL
#from fnmatch import filter
INCREMENT_DEAL_VIEW_URL = '/tasks/incrementDealView'

#creates a url for remote or local server
if os.environ['SERVER_SOFTWARE'].startswith('Development') == True:
	#we are on the development environment
	host_url = 'http://localhost:8080/'
else:
	#we are deployed on the server
	host_url = 'http://www.levr.com/'

class BaseHandler(webapp2.RequestHandler):
	'''
	Base class for webapp request handlers
	Mostly used for basic i/o
	'''
	def send_error(self,message='Server Error'):
		'''
		Just being used as a wrapper while code is migrating
		'''
		send_error(self,str(message))
		
	def send_fail(self,log_message=''):
		'''
		Used for server error. Registers an error in the logs before
		  returning an error
		@param message: error message
		@type message: str
		'''
		# register error in logs
		levr.log_error(log_message)
		
		# return an error
		self.send_error()
		
		
	def send_response(self,response,user=None):
		'''
		This is just being used as a wrapper until all classes can be migrated
		to using a BaseHandler inheritance
		'''
		send_response(self,response, user)
		
class Search(object):
	'''
	Base class for all search handlers
	'''
	min_levr_deals = 5
	foursquare_token = random.choice([
					'IDMTODCAKR34GOI5MSLEQ1IWDJA5SYU0PGHT4F5CAIMPR4CR',
					'ML4L1LW3SO0SKUXLKWMMBTSOWIUZ34NOTWTWRW41D0ANDBAX',
					'RGTMFLSGVHNMZMYKSMW4HYFNEE0ZRA5PTD4NJE34RHUOQ5LZ'
					])
	def __init__(self,development,user = None):
		# if the user has a token, override default selection of random dev token
		# set namespace to active or test
		self.development = development
		if self.development:
			self.deal_status = levr.DEAL_STATUS_TEST
		else:
			self.deal_status = levr.DEAL_STATUS_ACTIVE
		
		# try to add a user and grab their fs token if the have one
		# otherwise the foursquare token defaults to a random one
		self.user = user
		try:
			self.foursquare_token = user.foursquare_token
		except:
			pass
		
	def check_for_promotions(self,deals,user=None):
		'''
		A function to check search results for any promotions that might apply
		
		@status: Only handles a radius blast alert
		'''
		# TODO: if the user is a developer, do not check alert
		# Find deals that have a radius blast promotion
		#	and that have not been blasted to this user before
		promoted_deals = filter(lambda x: promo.RADIUS_ALERT in x.promotions,deals)
		logging.info('promoted_deals: {}'.format(promoted_deals))
		# Filter deals that have already been sent to the user via alert
		promoted_deals = filter(lambda x: x.key() not in user.been_radius_blasted,promoted_deals)
		logging.info('promoted_deals: {}'.format(promoted_deals))
		if promoted_deals:
			# select only one deal to blast
			deal = random.choice(promoted_deals)
			# create the notification for the deal
#			user = levr.Notification().create_radius_alert(user, deal)
			to_be_notified = user
			levr.Notification().radius_alert(to_be_notified, deal)
			# TODO: test new notification
		return user
	def calc_precision_from_half_deltas(self,geo_point,lon_half_delta=0):
		'''
		Determines a geohash precision from the lat and long half deltas
		
		@type lat_half_delta: float
		@type lon_half_delta: float
		@return: time of operation
		@rtype: datetime
		'''
		precision = 5
		if lon_half_delta >0:
	#		max([lat_half_delta,lon_half_delta])
			center_right_lat = geo_point.lat
			center_right_lon = geo_point.lon + lon_half_delta
			center_left_lat = geo_point.lat
			center_left_lon = geo_point.lon - lon_half_delta
			# calculate the width in miles of the screen
			width_in_miles = distance_between_points(center_right_lat,center_right_lon,center_left_lat,center_left_lon)
			
			if width_in_miles <2:
				precision = 6
		return precision
	def expand_ghash_list(self,ghash_list,n):
		'''
		Expands self.ghash n times
		@param n: number of expansions
		@type n: int
		'''
		for i in range(0,n): #@UnusedVariable
			# expand each ghash, and remove duplicates to expand a ring
			new_ghashes = []
			for ghash in ghash_list:
				new_ghashes.extend(geohash.expand(ghash))
			# add new hashes to master list
			ghash_list.extend(new_ghashes)
			# remove duplicates
			ghash_list = list(set(ghash_list))
		return ghash_list
	def create_ghash_list(self,geo_point,precision):
		'''
		
		'''
		
		ghash = geohash.encode(geo_point.lat, geo_point.lon, precision)
		ghash_list = [ghash]
		
		# determine number of iterations based on the precision
		if precision == 6:
			n = 3
		else:
			n = 1
		ghash_list = self.expand_ghash_list(ghash_list, n)
		return ghash_list
	def calc_bounding_box(self,ghash_list):
		'''
		Calculates a bounding box from a list of geohashes
		@param ghash_list: a list of geo_hashes
		@type ghash_list: list
		@return: {'bottom_left':<float>,'top_right':<float>}
		@rtype: dict
		'''
		points = [geohash.decode(ghash) for ghash in ghash_list]
		
		# calc precision from one the ghashes
		precision = max([ghash.__len__() for ghash in ghash_list])
		
		#unzip lat,lons into two separate lists
		lat,lon = zip(*points)
		
		#find max lat, long
		max_lat = max(lat)
		max_lon = max(lon)
		#find min lat, long
		min_lat = min(lat)
		min_lon = min(lon)
		
		# encode the corner points
		bottom_left_hash = geohash.encode(min_lat,min_lon,precision)
		top_right_hash = geohash.encode(max_lat, max_lon, precision)
		
		# get bounding boxes for the corner hashes
		tr = geohash.bbox(top_right_hash)
		bl = geohash.bbox(bottom_left_hash)
		# get the corner coordinates for the two corner hashes
		top_right = (tr['n'],tr['e'])
		bottom_left = (bl['s'],bl['w'])
		# compile into dict
		bounding_box = {
					'bottom_left'	: bottom_left,
					'top_right'		: top_right
					}
		return bounding_box
	def fetch_deals(self,ghash_list):
		'''
		Fetches deal entities from the db by their ghashes
		Filters out deals that are nonetype
		
		@todo: filter nonetype deals
		@return: deals and the bounding box of the search
		@rtype: list,dict
		'''
		# get keys
		deal_keys = get_deal_keys(ghash_list,development=self.development)
		
		# fetch deal entities
		deals = db.get(set(deal_keys))
		
		return deals
	
	def sort_deals(self,deals):
		'''
		Calculates the ranks of each deal.
		Assigns rank as a property to the deal
		@return: deals
		@rtype: list
		'''
		for deal in deals:
			# calculate total karma
			karma = deal.upvotes - deal.downvotes + deal.karma
			# add bias towards levr deals
			if deal.origin == 'levr' or deal.origin == 'merchant':
				karma += 5
			# set the deal rank as the karma
			deal.rank = karma
#			logging.debug('deal.rank = '+str(deal.rank))
		
		# sort the deals
		ranks = [d.rank for d in deals]
		toop = zip(ranks,deals)
		toop = sorted(toop,reverse=True)
		ranks,deals = zip(*toop)
		logging.info(ranks)
		return deals,ranks
	def filter_deals_by_query(self,deals,query):
		'''
		Splits the deals into two lists of accepted and rejected deals
			based on the query tags
		If no deals match, is_empty is set to True, and all deals are returned
		@param deals:
		@type deals:
		@param query: the query string
		@type query: str
		@return: num_results, which is the number of applicable deals from the query
		@rtype
		'''
		search_tags = levr.create_tokens(query)
		
		accepted_deals = []
		# compile list of deals whose tags match at least one tag
		if query != 'all':
			for deal in deals:
				deal_tags = deal.tags
				for tag in deal_tags:
					# if a tag matches, will add to accepted deals
					# TODO: rank deals by similarity frequency
					if tag in search_tags:
						accepted_deals.append(deal)
						break
			# count all of the applicable deals
			num_results = accepted_deals.__len__()
			
		else:
			# if no acceptable deals are found, return all of the deals
			accepted_deals = deals
			# count the number of applicable levr deals
			num_results = accepted_deals.__len__()
		
		return num_results,accepted_deals
	def add_deal_views(self,deals):
		'''
		Adds a deal view for each deal
		@param deals:
		@type deals:
		'''
		try:
			payload = {
					'deal_keys' : [str(deal.key()) for deal in deals]
					}
			taskqueue.add(url=INCREMENT_DEAL_VIEW_URL,payload=json.dumps(payload))
		except:
			levr.log_error()
	def sort_and_package(self,deals):
		'''
		Wrapper around the package_deals_multi
		Pulls out the ranks from the deals to send
		Sorts deals based on their rank
		@param deals:
		@type deals:
		'''
		if deals:
			deals,ranks = self.sort_deals(deals)
			# sort deals based on their ranks
			
			# package
			packaged_deals = package_deal_multi(deals, ranks=ranks)
		else:
			packaged_deals = []
		return packaged_deals


#@deprecated
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
#@deprecated
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

def package_deal_multi(deals,private=False,**kwargs):
	'''
	Batch packages a list of deals - prefetching related entities
	
	@param deals: The deal entities to be packaged for output
	@type deals: [levr.Deal,]
	@param private: Determines the privacy level of the information
	@type private: boolean
	'''
#	assert type(deals) == list, 'Must pass deals as a list; type = '+str(type(deals))
	logging.info(' PACKAGE DEAL MULTI')
	# Remove deals that do not exist
	deals = filter(lambda x: x,deals)
	
	# deal meta information
	# will be lists of [None,] if not passed as kwargs
	ranks = kwargs.get('ranks',[None for deal in deals]) #@UnusedVariable
	distances = kwargs.get('distances',[None for deal in deals]) #@UnusedVariable
	
	
	
	bad_deals = []
	# prefetch deal owners
	
	logging.info('Owners')
	owner_keys = [deal.key().parent() for deal in deals]
	owners = db.get(owner_keys)
	logging.debug(owners)
	logging.debug(owner_keys)
	
	
	# prefetch deal businesses
	business_keys = [deal.businessID for deal in deals]
	businesses = db.get(business_keys)
	logging.debug('Businesses')
	logging.debug(businesses)
	logging.debug(business_keys)
	
	# Remove deals that have bad references...
	data = zip(deals,owners,businesses,ranks,distances)
	logging.debug('data:')
	logging.debug(data)
	# Remove deals without valid owners
	data_sans_Nonetype_owners = filter(lambda x: x[1] is not None,data)
	# Remove deals without valid businesses
	new_data = filter(lambda x: x[2] is not None,data_sans_Nonetype_owners)
	
	logging.debug('postdata: ')
	logging.debug(new_data)
	
	# Notify the benevolent server monitors that there is some missing shit in here. BAD!
	if data != new_data:
		bad_deals = filter(lambda x: x not in new_data,data)
		logging.error('There are deals with missing references: ')#+str([deal.key() for deal in deals]))
		for bd in bad_deals:
			logging.error(bd[0].deal_text)
			logging.error(bd[0].key())
			
	
	# if there were any bad references, log them
	# Continue without the filtered deals
	logging.info(new_data)
	return package_prefetched_deal_multi(new_data, private)
	
def package_prefetched_deal_multi(data,private=False):
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
	
	if rank is not None:
		packaged_deal['rank'] = rank
	if distance is not None:
		packaged_deal['distance'] = distance
	
	if private == True:
		
		packaged_deal.update({
							'views'	: deal.views,
							'promotions' : [promo.PROMOTIONS[p] for p in deal.promotions],
							'status': deal.deal_status
							})
	
	return packaged_deal
	
def package_deal(deal,private=False,**kwargs):
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
	if private:
		pass
# 	if private:
# 		packaged_user.update({
# 							'moneyAvailable'	: 1,
# 							'moneyEarned'		: 1,
# 							})
	
	return packaged_user
def package_notification_multi(notifications):
	'''
	@param notifications: a list of notification entities
	@type notifications: list
	@return: a list of packaged notiications
	@rtype: list
	'''
	packaged_notifications = [package_notification(notification) for notification in notifications]
	
	return packaged_notifications
	
def package_notification(notification):
	'''
	Switch case on notification based on the version of notification, old or new
	@param notification: Notification entity
	@type notification: levr.Notification
	'''
	# New notifications
	if notification.model_version == 2:
		return notification.package()
	else:
		return _package_notification(notification)
def _package_notification(notification):
	packaged_notification = {
		'notificationID'	: enc.encrypt_key(str(notification.key())),
#		'date'				: str(notification.date)[:19],
		'date'				: notification.date_in_seconds,
		'notificationType'	: notification.notification_type,
		'line2'				: notification.line_2,
		'user'				: package_user(notification.actor),
#		'notificationID'	: enc.encrypt_key(notification.key())
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
def fetch_all_users_deals(user):
	deals = levr.Deal.all().ancestor(user).fetch(None)
	logging.debug('deals length: '+str(deals.__len__()))
	
	if user.tester:
		deal_status = 'test'
	else:
		deal_status = 'active'
	
	# separate the two kinds of deals
	active_deals = filter(lambda x: x.deal_status == deal_status,deals)
	expired_deals = filter(lambda x: x.deal_status == 'expired',deals)
	
	# sort the active and expired deals by their respecive sort properties
	active_deals = sort_deals_by_property(active_deals, 'date_last_edited')
	expired_deals = sort_deals_by_property(expired_deals, 'date_end')
	
	# combine the two lists of deals into one
	all_deals = []
	all_deals.extend(active_deals)
	all_deals.extend(expired_deals)
	
	return all_deals
def fetch_all_businesses_deals(business,development=False):
	'''
	Fetches all of the deals from a business
	@param business:
	@type business:
	'''
	if development == True:
		deal_status = levr.DEAL_STATUS_TEST
	else:
		deal_status = levr.DEAL_STATUS_ACTIVE
	
	deals = levr.Deal.all().filter('businessID',str(business.key())).filter('deal_status',deal_status).fetch(None)
		
	return deals
def sort_deals_by_property(deals,prop):
	if deals:
		extracted_props = [getattr(deal,prop) for deal in deals]
		toop = zip(extracted_props,deals)
		sorted_toop = sorted(toop)
		sorted_props, deals = zip(*sorted_toop) #@UnusedVariable: sorted_props
	return deals

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

def validate(url_param,authentication_source,*a,**to_validate): #@UnusedVariable
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
						'foursquareID'		: str,
						
						
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
						'daysToExpire'	: int,
						
						#business upload stuff
						'businessName'	: str,
						#geoPoint ^^ see above
						'vicinity'		: str,
						'types'			: str,
						'shareURL'		: str,
						'phoneNumber'	: str,
						
						#promotion stuff
						'tags'			: list,
						'promotionID'	: str,
						'receipt'		: str,
						
						# other
						'ignored'		: str
						
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
						'foursquareID'		: '',
						
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
						'daysToExpire'	: 7,
						
						#business upload stuff
						'businessName'	: '',
						'vicinity'		: '',
						'types'			: '',
						'shareURL'		: '',
						'phoneNumber'	: '',
						
						# Promotion stuff
						'tags'			: [],
						'promotionID'	: '',
						'receipt'		: '',
						
						# other
						'ignored'		: '',
						
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
#						levr.log_error()
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
#						levr.log_error()
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
						
#						logging.debug(uid)
#						logging.debug(required)
						
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
				
				if self.request.get('ll'):
					sent_as_ll = True
				else:
					sent_as_ll = False
				#for each input=Bool where Bool is required or not
				for (key,required) in to_validate.iteritems():
					#special case, geopoint is complex
					if key == 'geoPoint':
						if not sent_as_ll:
							# ll was sent as lat=&lon=
							val = str(self.request.get('lat'))+","+str(self.request.get('lon'))
						else:
							key = 'ignored'
							val = ''
						msg = "lat,lon: "+val
					elif key == 'll':
						if sent_as_ll:
							val = str(self.request.get('ll'))
							msg = 'll: '+val
						else:
							key = 'ignored'
							val = ''
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
					
					#===========================================================
					# Operations
					#===========================================================
					
					#requires is whether or not it is required
					required	= to_validate.get(key)
					#date_type pulls the type that the passed input should be
					try:
						data_type	= type_cast[key]
					except:
						levr.log_error('did not map type_cast dict correctly')
						raise Exception()
					#msg is passed to the exception handler if val fails validation
					
#					logging.debug(msg)
#					logging.debug(data_type)
#					logging.debug(required)
					
					#handle case where input is not passed
					
					if 		not val and required				: raise KeyError(msg)
					elif 	not val and not required			: val = defaults[key]
					
					#handle case where input should be an integer
					elif data_type == int: 
						try:
							#convert to int
							val = int(val)
						except:
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
							key = 'geoPoint'
							logging.debug('---')
							logging.info(key)
							logging.info(val)
							logging.debug('---')
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
					logging.debug(key)
					logging.debug(val)
					kwargs.update({key:val})
				
				logging.debug(kwargs)
			
			except AttributeError,e:
#				levr.log_error()
				send_error(self,'Not Authorized, '+str(e))
			except KeyError,e:
#				levr.log_error()
				send_error(self,'Required paramter not passed, '+str(e))
			except TypeError,e:
#				levr.log_error()
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
	if namespace is not None:
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

def create_bounding_box(lat, lon, distance): #@UnusedVariable
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
@levr.deprecated
def search_foursquare(geo_point,token,deal_status,already_found=[],**kwargs):
	assert deal_status != 'random', 'Deal status is being set as random'
	#if token is passes as 'random', use a hardcoded token
	if not token or token == 'random':
		hardcoded = ['IDMTODCAKR34GOI5MSLEQ1IWDJA5SYU0PGHT4F5CAIMPR4CR','ML4L1LW3SO0SKUXLKWMMBTSOWIUZ34NOTWTWRW41D0ANDBAX','RGTMFLSGVHNMZMYKSMW4HYFNEE0ZRA5PTD4NJE34RHUOQ5LZ']
		token = random.choice(hardcoded)
	logging.info('Using token: '+token)
	
	
	url = 'https://api.foursquare.com/v2/specials/search?v=20120920&ll='+str(geo_point)+'&limit=50&oauth_token='+token
	result = urlfetch.fetch(url=url)
	if result.status_code != 200:
		# Foursquare request was not successful
		logging.debug(result.content)
		logging.error('Failed response from foursquare with code: '+repr(result.status_code))
		logging.error(result.headers.data)
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
		if not filter_foursquare_deal(foursquare_deal,already_found): # returns True if the deal is filtered out
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
				logging.info('Foursquare special '+foursquare_deal['id']+' NOT found in database'+ str(' '))
				#add the foursquare deal
				deal = add_foursquare_deal(foursquare_deal,business,deal_status)
			
			else:
				deal = existing_deal
				logging.info('Foursquare special '+deal.foursquare_id+' found in database but not in search. '+ repr(deal.deal_text))
#				logging.debug('foursquare')
				#logging.debug(levr.log_model_props(deal))
			deal_business = db.get(deal.businessID)
			#calculate distance
			distance = distance_between_points(geo_point.lat, geo_point.lon, deal_business.geo_point.lat, deal_business.geo_point.lon)
			#calculate distance
			distance2 = distance_between_points(geo_point.lat, geo_point.lon, business.geo_point.lat, business.geo_point.lon)

# 			logging.debug('DISTANCE!!!: '+str(distance))
			logging.debug('distance: '+repr(distance)+ ' or '+ repr(distance2))
			logging.warning('geopoint1: '+repr(deal_business.geo_point)+', geopoint2: '+ repr(business.geo_point))
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

@levr.deprecated
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
		business		=	business,
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


	deal.put()
	
	logging.debug(levr.log_model_props(deal, ['deal_text','foursquare_id','businessID','deal_text']))
	
	
	#===========================================================================
	# Update memcache because a deal was created
	#===========================================================================
	levr.remove_memcache_key_by_deal(deal)
	
	
	logging.info('Foursquare special '+deal.foursquare_id+' added to database.')
	#logging.debug(levr.log_model_props(deal))
	
	return deal


def filter_foursquare_deal(foursquare_deal,already_found):
	'''
	
	@param foursquare_deal: The response from foursquare - the deal
	@type foursquare_deal: dict
	@param already_found: The list of deals that were already found in the db...?
	@type already_found: list
	
	
	@return: Whether or not the deal was found in the db - If found, return True
	@rtype: bool
	'''
	
# 	allowed_categories = ["Afghan Restaurant", "African Restaurant", "American Restaurant", "Arepa Restaurant", "Argentinian Restaurant", "Asian Restaurant", "Australian Restaurant", "BBQ Joint", "Bagel Shop", "Bakery", "Brazilian Restaurant", "Breakfast Spot", "Brewery", "Burger Joint", "Burrito Place", "Caf\u00e9", "Cajun / Creole Restaurant", "Caribbean Restaurant", "Chinese Restaurant", "Coffee Shop", "Cuban Restaurant", "Cupcake Shop", "Deli / Bodega", "Dessert Shop", "Dim Sum Restaurant", "Diner", "Distillery", "Donut Shop", "Dumpling Restaurant", "Eastern European Restaurant", "Ethiopian Restaurant", "Falafel Restaurant", "Fast Food Restaurant", "Filipino Restaurant", "Fish & Chips Shop", "Food Truck", "French Restaurant", "Fried Chicken Joint", "Gastropub", "German Restaurant", "Gluten-free Restaurant", "Greek Restaurant", "Hot Dog Joint", "Ice Cream Shop", "Indian Restaurant", "Indonesian Restaurant", "Italian Restaurant", "Japanese Restaurant", "Juice Bar", "Korean Restaurant", "Latin American Restaurant", "Mac & Cheese Joint", "Malaysian Restaurant", "Mediterranean Restaurant", "Mexican Restaurant", "Middle Eastern Restaurant", "Molecular Gastronomy Restaurant", "Mongolian Restaurant", "Moroccan Restaurant", "New American Restaurant", "Peruvian Restaurant", "Pizza Place", "Portuguese Restaurant", "Ramen / Noodle House", "Restaurant", "Salad Place", "Sandwich Place", "Scandinavian Restaurant", "Seafood Restaurant", "Snack Place", "Soup Place", "South American Restaurant", "Southern / Soul Food Restaurant", "Spanish Restaurant", "Steakhouse", "Sushi Restaurant", "Swiss Restaurant", "Taco Place", "Tapas Restaurant", "Tea Room", "Thai Restaurant", "Turkish Restaurant", "Vegetarian / Vegan Restaurant", "Vietnamese Restaurant", "Winery", "Wings Joint", "Bar", "Beer Garden", "Cocktail Bar", "Dive Bar", "Gay Bar", "Hookah Bar", "Hotel Bar", "Karaoke Bar", "Lounge", "Nightclub", "Other Nightlife", "Pub", "Sake Bar", "Speakeasy", "Sports Bar", "Strip Club", "Whisky Bar", "Wine Bar"]
	
	
#	logging.info('---------------------------------------------')
#	logging.info('Type: '+foursquare_deal['type'])
#	logging.info('Message: '+foursquare_deal['message'])
#	logging.info('Description: '+foursquare_deal['description'])
#	logging.info('Category: '+foursquare_deal['venue']['categories'][0]['name'])
	
	allowed_types = ['count','regular','flash','swarm','other','frequency']	#not mayor
	
# 	logging.debug(foursquare_deal['venue']['categories'])
	
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
	

def rotate_image(blob_key,deal=None):
	'''
	Checks the orientation of an image in the blobstore.
	If the image is rotated, rotate it again until it is in a natural orientation
	
	@param blob_key: The blob key for the image that is being checks
	@type blob_key: blobstore blob_key
	
	@return: Nothing.
	'''
	blob = blobstore.BlobInfo.get(blob_key)
	
	img = images.Image(blob_key=blob_key)

	#execute a bullshit transform
	img.rotate(0)
	img.execute_transforms(output_encoding=images.JPEG,quality=100,parse_source_metadata=True)
	
	#self.response.headers['Content-Type'] = 'image/jpeg'
	#THIS LINE WILL FAIL IF YOU TRY CALL THIS ON AN IMAGE THAT HAS PREVIOUSLY BEEN ROTATED
	test_dict = img.get_original_metadata()
	if 'Orientation' in test_dict:
		
		orient = img.get_original_metadata()['Orientation']
		
		if orient != 1:
			logging.info('Image not oriented properly')
			logging.info('Orientation: '+str(orient))
			if orient == 6:
				#rotate 270 degrees
				img.rotate(90)
			elif orient == 8:
				img.rotate(270)
			elif orient == 3:
				img.rotate(180)
		
			#write out the image
			output_img = img.execute_transforms(output_encoding=images.JPEG,quality=100,parse_source_metadata=True)
		
			#figure out how to store this shitttt
			# Create the file
			overwrite = files.blobstore.create(mime_type='image/jpeg')
			
			# Open the file and write to it
			with files.open(overwrite, 'a') as f:
				f.write(output_img)
			
			# Finalize the file. Do this before attempting to read it.
			files.finalize(overwrite)
			
			# Get the file's blob key
			new_blob_key = files.blobstore.get_blob_key(overwrite)
			
			if deal is None:
				#grab the reference to the old image
				deal = levr.Deal.gql('WHERE img=:1',blob_key).get()
			logging.debug('Old img key: '+str(blob_key))
			logging.debug('New img key: '+str(new_blob_key))
			deal.img = new_blob_key
			logging.debug(deal.img)
			deal.put()
			logging.debug('Deal updated')
			
			#delete the old blob
			blob.delete()
			logging.debug('Old image deleted successfully')
		else:
			logging.info('Image oriented properly')
	else:
		logging.info('No "Orientation" property found in Exif data - this image must have been rotated previously')
		
class KWLinker(object):
	'''
	A class to register relationships between keywords
	
	@todo: remove false keywords, e.g. popular,all
	'''
	# the relational weight that a click on a deal has
	_click_strength = 1
	# the relational weight that a like on a deal has
	_like_strength = 3
	# the relational weight that a manual categorization by admin has
	_admin_strength = 5
	
	def __init__(self,development):
		'''
		
		@param development: Whether or not we are in the development namespace
		@type development: bool
		'''
		self.development = development
		
	#===========================================================================
	# Actions
	#===========================================================================
	@classmethod
	def register_deal_click(cls,deal,query):
		'''
		Registers a click on a deal that was found for a particular query
		@param deal: the deal entity that was clicked
		@type deal: levr.Deal
		@param query: the actual search query
		@type query: str
		'''
		try:
			strength = cls._click_strength
			cls._create_link_from_query(query, deal, strength)
			return True
		except:
			levr.log_error('Error in registering a deal click; deal: {}, query: {}'.format(
							deal.key(),query
							)
						)
			return False
	@classmethod
	def register_like(cls,deal,query):
		'''
		Registers a like on a deal from a particular query
		@param deal: deal that was liked
		@type deal: levr.Deal
		@param query: search query
		@type query: str
		'''
		try:
			strength = cls._like_strength
			cls._create_link_from_query(query, deal, strength)
			return True
		except:
			levr.log_error('Error in registering a deal like; deal: {}, query: {}'.format(
							deal.key(),query
							)
						)
			return False
	@classmethod
	def register_categorization(cls,deal,parent_tags,stemmed):
		'''
		An admin manually categorized this deal, relating it to a list of tags
		If stemmed is passed as False, then the parent_tags are stemmed
		
		@param deal: the deal that was categorized
		@type deal: levr.Deal
		@param parent_tags: The list of keywords that are related to the deal
		@type parent_tags: list
		@param stemmed: Whether or not the parent_tags have already been stemmed
		@type stemmed: bool
		'''
		assert type(parent_tags) == list, 'parent tags must be a list: '+str(type(parent_tags))
		parent_tags = [x.lower() for x in parent_tags]
		if stemmed == False:
			parent_tags = levr._stem(parent_tags)
		
		
		strength = cls._admin_strength
		children_tags = deal.tags
		cls._create_link_to_tags_multi(parent_tags, children_tags, strength)
	#===========================================================================
	# Utilities
	#===========================================================================
	@classmethod
	def _create_link_from_query(cls,query,deal,strength):
		'''
		Someone performed an action on a deal after performing a search
		
		@param query: A space delimited sequence of keywords
		@type query: str
		@param deal: The deal that an action was performed on, causing this link
		@type deal: levr.Deal
		@param strength: The strength of the keyword relationship that is to be addeded
		@type strength: int
		'''
		parent_tags = levr.create_tokens(query)
		children_tags = deal.tags
		cls._create_link_to_tags_multi(parent_tags, children_tags, strength)
	@classmethod
	def _create_link_to_tags_multi(cls,parent_tags,children_tags,strength):
		'''
		Wrapper for self.create_link_to_tags to handle multiple parent tags at once
		
		@warning: parent_tags must be tokenized
		
		@param parent_tags: The tokenized search query
		@type parent_tags: list
		@param children_tags: the tags that are to be related to the parent tags
		@type children_tags: list
		'''
#		assert type(parent_tags) == list, 'parent_tags must be <type \'list\'>.'
		logging.info(parent_tags)
		# typecast parent_tags as list
		# otherwise, e.g. 'Food' will be broken up into 'f','o','o','d'
		if type(parent_tags) == str or type(parent_tags) == unicode:
			parent_tags = [parent_tags]
#		assert False, '{}:{}'.format(parent_tags,type(parent_tags))
		# remove duplicates
		
		parent_tags = list(set(parent_tags))
		
		for parent_tag in parent_tags:
			cls._create_link_to_tags(parent_tag, children_tags,strength)
		
	@classmethod
	def _create_link_to_tags(cls,parent_tag,children_tags,strength):
		'''
		Creates a one-way relationship linking the parent tag node to the children tags
		If the parent node does not exist yet, it creates it.
		If the link does not exist yet, it creates it.
		
		@warning: the parent tag must be tokenized
		@warning: the children_tags must be tokenized
		
		@param parent_tag: The keyword that is being linked TO
		@type parent_tag: str
		@param children_tags: The stemmed and filtered keywords that are being linked to the parent
		@type children_tags: list
		@param strength: the link strength that is being added
		@type strength: int
		'''
		# if the parent node does not exist, create it
		parent_node = levr.KWNode.get_or_insert(parent_tag)
		
		assert parent_node, 'parent node not created'
#		try:
			# transactionally increment the 
		cls._increment_links(parent_node, children_tags,strength)
#		except:
#			# the transaction failed.
#			levr.log_error('Linkage failed for node: '+str(parent_tag))
#			return False
#		else:
#			return True
	#===========================================================================
	# Base utility.
	#===========================================================================
	@staticmethod
	@ndb.transactional(retries=10)
	def _increment_links(parent_node,children_tags,strength):
		'''
		Increments the strength of KWLinks specified by the children_tags
		Creates a KWLink entity for each of the children_tags, if they do not exist already
		Increments the link strength by the value that is provided
		
		Transaction runs n times (see decorator) until it is successful
		If the transaction fails too many times, it will raise an error
		
		@param parent_node: The KWNode entry
		@type parent_node: levr.KWNode
		@param children_tags: The KWs that are being linked to the parent
		@type children_tags: list or str
		@param strength: The amount to increment the link strength by
		@type strength: int
		'''
		# If a single tag was passed, convert it to a list
		if type(children_tags) != list:
			children_tags = list(children_tags)
		
		# fetch each of the linkages 
		node_links = [levr.KWLink.get_or_insert(tag,parent=parent_node.key)
					for tag in children_tags if tag != parent_node.name]
		# do not link the node to itself
		for link in node_links:
			link.strength += strength
		ndb.put_multi(node_links)


class PromoteDeal(BaseHandler):
	'''
	Class for promoting deals.
	@todo: make this a standalone class, remove webapp request handler inheritance
	'''
	def __initialize__(self,deal,user,**kwargs):
		'''
		This is named _initialize__ instead of init because of the
		way that webapp2 creates an instance of the class before the
		actual rpc call to my handler.
		
		
		@param deal: The deal being promoted
		@type deal: Deal
		@param purchaser: The Customer who purchased the promotion
		@type purchaser: Customer
		@param promotion_id: The form of promotion being applied
		@type promotion_id: str
		
		@keyword development: A flag to run this in development mode
			If true, will only affect test deals and test people
		@type development: bool
		'''
		self.deal = deal
		self.user = user # user is the purchaser of the promotion
#		self.promotion_id = promotion_id
		
		# set the business
		try:
			logging.debug(deal.business)
			if self.deal.business:
				self.business = self.deal.business
			else:
				self.business = levr.Business.get(self.deal.businessID)
		except:
			
			logging.debug(levr.log_model_props(deal))
			self.business = levr.Business.get(self.deal.businessID)
		
		
		# if the purchaser is a development account, then act in development mode
		self.development = user.tester
		
	def check_self(self):
		logging.debug(levr.log_model_props(self.deal))
		logging.debug(levr.log_model_props(self.business))
		logging.debug(levr.log_model_props(self.purchaser))
	
	
	def get_all_deals_response(self):
		'''
		Packages all deals into a json
		
		@return: the base json for the reply in merchants api
		@rtype: dict
		'''
		private = True
		deals = fetch_all_users_deals(self.user)
		packaged_deals = package_deal_multi(deals, private)
		
		response = {
				'deals'	: packaged_deals
				}
		return response
	def get_promotion_by_promotionID(self,promotion_id):
		'''
		Pulls a promotion for self.deal from the db based on the promotionID
		@param promotionID: promotion identifier
		@type promotionID: str
		
		@return: A promotion entity
		@rtype: levr.DealPromotion
		'''
		key_name = self.make_promo_key_name(promotion_id)
		promotion_entity = levr.DealPromotion.get_by_key_name(key_name)
		return promotion_entity
	def make_promo_key_name(self,promotionID):
		'''
		Creates a key_name for a promotion entity using the uid and promotionID
		key_names are in form of <uid>|<promotionID>
		
		@param promotionID: the promotion identifier
		@type promotionID: str
		'''
		return '{}|{}'.format(self.deal.key(),promotionID)
	
	#===========================================================================
	# Return functions
	#===========================================================================
	def get_sans_put(self):
		'''
		Returns the deal as-is
		'''
		return self.deal
	def put(self):
		'''
		Simply puts the deal and returns the deal
		Useful for stacking promotions where it is undesirable to
			put the deal every time a promotion is applied
		'''
		self.deal.put()
		return self.deal
	def _return(self,auto_put=True):
		'''
		Wrapper for the return function
		simply for determining if the deal or the PromoteDeal object should be returned
		
		@keyword auto_put: if true, will return the deal
		@type auto_put: bool
		'''
		if auto_put == True:
			self.deal.put()
			return self.deal
		else:
			return self
	_max_sub_query_length = 30
	def _reduce_queries(self,lst):
		'''
		When a query like db.Model.all().filter(ListProperty,<type 'list'>).fetch(None)
		  is run, it creates a number of sub-queries equal to the number of list items
		  in the filter.
		
		It can only support a maximum of _max_sub_query_length.
		To prevent our promotion calls from failing, we limit the number of sub-queries
		  that are generated by reducing the length of the list we use to query
		
		@param lst: The list of properties that are being queried
		@type lst: list
		'''
		if lst and lst.__len__() > self._max_sub_query_length:
			lst = lst[:self._max_sub_query_length]
			logging.warning('A promotion to alert some users resulted in clipping some \
			deals because the business owns too many deals.')
			logging.warning(levr.log_model_props(self.user))
			logging.warning(levr.log_model_props(self.business))
			logging.warning(levr.log_model_props(self.deal))
		return lst
	
	#===========================================================================
	# Interfaces with the promotion entity in the db
	#===========================================================================
	def _add_promo(self,promotion_id):
		'''
		Adds the promotion to the list of promotions
		Also creates a promotion entity to log the event
		
		@param promo_type: one of the available promotions
		@type promo_type: str
		'''
		self.deal.promotions.append(promotion_id)
		name = self.make_promo_key_name(promotion_id)
		
		promotion = levr.DealPromotion(
							key_name = name,
							purchaser = self.user,
							deal = self.deal,
							promotion_id = promotion_id
							)
		# add the deal tags to the promotion
		if promotion_id == promo.MORE_TAGS:
			if not self.tags:
				logging.error('No self.tags were passed to Promotion._add_promo')
			promotion.tags = list(self.tags)
		promotion.put()
		return
	def _remove_promo(self,promotion_id):
		'''
		Removes a promotion from the list of promotions on a deal
		deletes the promotion entity that was created in _add_promo
		
		@param promotionID: one of the available promotions
		@type promotionID: str
		'''
		# remove the promo entity
		promo_entity = self.get_promotion_by_promotionID(promotion_id)
		
		# remove tags
		tags = promo_entity.tags
		if tags:
			for tag in tags:
				try:
					self.deal.extra_tags.remove(tag)
				except ValueError,e:
					logging.error('A tag could not be removed from a deal. This should not happen')
					logging.info('deal key: '+str(self.deal.key()))
					logging.info('tag: '+str(tag))
					logging.info('deal tags: '+str(self.deal.extra_tags))
					levr.log_error(e)
					
		
		promo_entity.delete()
		
		# remove promo id from the deal entity
		self.deal.promotions.remove(promotion_id)
		return
		
		
	
	#===========================================================================
	# Actions!
	#===========================================================================
	def run_promotion(self,promotion_id,**kwargs):
		'''
		Runs the promotion that is specified by the promo_type
		Pass the arguments required for any of the promotion functs
			to this, and it will be sent via args,kwargs
		
		@param promotion_id: The promotion identifier
		@type promotion_id: str
		@keyword auto_put: determines whether to put the deal before returning or not
		
		@return: depends on the function that is called
		'''
			
		# make sure the promotion has not been run
		assert promotion_id not in self.deal.promotions, \
			'Deal already has promotion: {}'.format(promotion_id)
		
		handlers = {
				promo.BOOST_RANK : self._set_boost_rank,
				promo.MORE_TAGS : self._set_more_tags,
				promo.NOTIFY_PREVIOUS_LIKES : self._set_notify_previous_likes,
				promo.NOTIFY_RELATED_LIKES : self._set_notify_related_likes,
				promo.RADIUS_ALERT : self._set_radius_alert
				}
		handler_args = {
					promo.MORE_TAGS : kwargs.get('tags'),
					}
		
		# Assure that the requested promotion is available for hire
		assert promotion_id in [key for key in handlers], \
			'Promotion not available: {}'.format(promotion_id)
		
		try:
			funct = handlers[promotion_id]
			try:
				# run the promotion with args
				args = handler_args[promotion_id]
				funct(args)
			except:
				# run the required function without args
				funct()
		except:
			levr.log_error()
			# run the promotion
			handlers[promotion_id]()
		# create the promotion entity
		self._add_promo(promotion_id)
		# return
		auto_put = kwargs.get('auto_put',True)
		return self._return(auto_put)
		
	def confirm_promotion(self,promotion_id,receipt,**kwargs):
		'''
		Confirms a promotion. Fetches the promotion entity and adds a receipt
		
		@param promotion_id: promotion identifier
		@type promotion_id: str
		'''
		promotion_entity = self.get_promotion_by_promotionID(promotion_id)
		# add the receipt to the promotion
		promotion_entity.receipt = receipt
		promotion_entity.put()
		auto_put = kwargs.get('auto_put',True)
		return self._return(auto_put)
	def remove_promotion(self,promotion_id,**kwargs):
		'''
		Runs the function to remove the effects of a promotion that
		 was previously run
		
		@param promotion_id: the promotion to be removed
		@type promotion_id: str
		'''
		# do nothing if the promotion has not been run..
		if promotion_id not in self.deal.promotions:
			return
		handlers = {
				promo.BOOST_RANK : self._remove_boost_rank,
				promo.MORE_TAGS : self._remove_more_tags,
				promo.NOTIFY_PREVIOUS_LIKES : self._remove_notify_previous_likes,
				promo.NOTIFY_RELATED_LIKES : self._remove_notify_related_likes,
				promo.RADIUS_ALERT : self._remove_radius_alert
				}
		# Assure that the requested promotion is available for hire
		assert promotion_id in [key for key in handlers], \
			'Promotion not available: {}'.format(promotion_id)
		
		# run the action
		handlers[promotion_id]()
		# Remove the promotion entity
		self._remove_promo(promotion_id)
		# Return
		auto_put = kwargs.get('auto_put',True)
		return self._return(auto_put)
	#===========================================================================
	# Promotions!!!
	#===========================================================================
	#===========================================================================
	# Boost Rank
	#===========================================================================
	_karma_boost = 200
	def _set_boost_rank(self):
		'''
		Gives the deal preference over other deals so that it is shown before them
		This is done by adding karma to the deal without increasing the upvotes
		'''
		# increase the unseen karma of the deal
		self.deal.karma += self._karma_boost
		return
	def _remove_boost_rank(self):
		'''
		Removes the karma from the deal that was added
		'''
		# remove karma
		self.deal.karma -= self._karma_boost
		return
	#===========================================================================
	# More Tags
	#===========================================================================
	def _set_more_tags(self):
		'''
		Increases the tags on a deal so that it is more visible
		'''
		# FIXME: passing tags like this is shitty. Better way?
		
		# append new deal tags to the list of tags
		assert type(self.tags) == list, 'tags must be a list'
		self.deal.extra_tags.extend(self.tags)
		return
	def _remove_more_tags(self):
		'''
		Removes the tags that were added by the _set_more_tags function
		'''
		# Do nothing here. All is taken care of by the self._remove_promo
		return
	#===========================================================================
	# Radius Alert
	#===========================================================================
	def _set_radius_alert(self):
		'''
		Sends a notification to ALL users within a certain radius when they search 
		'''
		# all actions are handled dynamically at the search, so do nothing here!
		return
	def _remove_radius_alert(self):
		'''
		Removes the effects from setting a radius alert
		'''
		# Do nothing here. All is taken care of in self._remove_promo
		#   because all actions taken for this promo happen at search time
		return
	#===========================================================================
	# Notify Previous Likes
	#===========================================================================
	def _set_notify_previous_likes(self):
		'''
		Sends a notification to everyone who has liked a deal at that business before
		'''
		# grab the business from the deal - already have self.business
		
		# get all deals that reference the business
		deal_keys = levr.Deal.all(keys_only=True).filter('businessID',str(self.business.key())).order('-deal_status').fetch(None)
		# deals = self.deal.buinsess.deals.fetch(None)
		logging.debug(deal_keys)
		# get all customers that have ever liked anything at that business before
		deal_keys = self._reduce_queries(deal_keys)
		
#		user_keys = levr.Customer.all(keys_only=True).filter('upvotes',deal_keys).fetch(None)
		# This sucks.
		user_keys = set([])
		for dk in deal_keys:
			user_keys.update(levr.Customer.all(keys_only=True).filter('upvotes',dk).fetch(None))
		to_be_notified = list(user_keys)
		
		# add a notification for each of the users
		levr.Notification().following_upload(to_be_notified, self.user, self.deal)
		
		# TODO: test new notification
		
		return
	
	def _remove_notify_previous_likes(self):
		'''
		Removes the actions taken by the set_notify_previous_likes
		'''
#		self.promotion_id = promo.NOTIFY_PREVIOUS_LIKES
		notification = levr.Notification.all(
											).filter('actor',self.user
											).filter('deal',self.deal
											).filter('notification_type','followedUpload'
											).get()
		if notification:
			notification.delete()
		return
	#===========================================================================
	# Notify Related Likes
	#===========================================================================
	def _set_notify_related_likes(self):
		'''
		Sends a notification to everyone who has likes a deal that is similar to this one
		
		'''
		# get deal tags
		tags = list(set(self.deal.tags))
		# get all deals with similar tags
		tags = self._reduce_queries(tags)
#		deal_keys = levr.Deal.all(keys_only=True).filter('tags',tags).order('-date_created').fetch(None)
		deal_keys = set([])
		for tag in tags:
			deal_keys.update(levr.Deal.all(keys_only=True).filter('tags',tag))
		deal_keys = list(deal_keys)
		deals = db.get(deal_keys)
		deals = sort_deals_by_property(deals, 'date_created')
		
		# get all customers that have liked any of the businesses before
		deal_keys = self._reduce_queries(deal_keys)
#		user_keys = levr.Customer.all(keys_only=True).filter('upvotes',deal_keys).fetch(None)
		user_keys = set([])
		for dk in deal_keys:
			user_keys.update(levr.Customer.all(keys_only=True).filter('upvotes',dk).fetch(None))
		to_be_notified = list(user_keys)
		# add a notification for all of the users
		levr.Notification().following_upload(to_be_notified, self.user.actor, self.deal)
		
		return
	def _remove_notify_related_likes(self):
		'''
		Removes the actions taken by the set_notify_related_likes
		'''
		# otherwise expunge the notifications
		notification = levr.Notification.all(
											).filter('actor',self.user
											).filter('deal',self.deal
											).filter('notification_type','followedUpload'
											).get()
		if notification:
			notification.delete()
		
		return

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
		
		
		
		
		
