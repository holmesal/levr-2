import json
import levr_encrypt as enc
import levr_classes as levr
import logging
from google.appengine.ext import db

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
def check_param(self,parameter,parameter_name,param_type='str',required=True):
	#check if parameter sent in params
	#parameter is passed
	logging.info(parameter_name+": "+str(parameter))
	if not parameter:
#		logging.info("EERRRRR")
		#parameter is empty
		if required == True:
			send_error(self,'Required parameter not passed: '+str(parameter_name))
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
				if required == True:
					send_error(self,'Invalid parameter: '+str(parameter_name)+"; "+str(parameter))
				return False
		elif param_type == 'int':
#			logging.debug('integer')
			if not parameter.isDigit():
				if required == True:
					send_error(self,'Invalid parameter: '+str(parameter_name)+"; "+str(parameter))
				return False
	logging.info(parameter_name+": "+str(parameter))
	return True

def package_deal(deal,privacyLevel='public'):
	logging.debug(str(deal.geo_point))
	packaged_deal = {
			'barcode'		: deal.barcode,
			'business'		: package_business(levr.Business.gql('WHERE businessID = :1',deal.businessID)),
			'dateUploaded'	: str(deal.date_end),
			'dealID'		: enc.encrypt_key(deal.key()),
			'dealText'		: deal.deal_text,
			'description'	: deal.description,
			'isExclusive'	: deal.is_exclusive,
			'largeImg'		: levr.create_img_url(deal,'large'),
			'geoHash'		: deal.geo_hash,
			'geoPoint'		: str(deal.geo_point),
			'redemptions'	: 'TODO!!',
			'smallURL'		: levr.create_img_url(deal,'small'),
			'status'		: deal.deal_status,
			'shareURL'		: levr.create_share_url(deal),
			'tags'			: deal.tags
			}
	return packaged_deal
def package_user(user,privacyLevel='public'):
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
		'photo'			: user.photo
	}
	
	return packaged_user
	
def package_business(business):
	packaged_business = {
		'businessID'	: enc.encrypt_key(str(business.key())),
		'businessName'	: business.business_name,
		'vicinity'		: business.vicinity,
		'owner'			: business.owner,
		'foursquareID'	: business.foursquare_id,
		'foursquareName': business.foursquare_name,
		'geoPoint'		: str(deal.geo_point),
		'geoHash'		: deal.geo_hash
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
	if os.environ['SERVER_SOFTWARE'].startswith('Development') == True:
		#we are on the development environment
		URL = 'http://localhost:8080/'
	else:
		#we are deployed on the server
		URL = 'http://www.levr.com/'
		
	share_url = URL+deal_entity.share_id
	return share_url
	
def create_img_url(deal_entity,size):
	#creates a share url for a deal
	if os.environ['SERVER_SOFTWARE'].startswith('Development') == True:
		#we are on the development environment
		img_url= 'http://localhost:8080/phone/img?dealID='+enc.encrypt_key(deal_entity.key())+'&size='+size
	else:
		#we are deployed on the server
		img_url = 'http://www.levr.com/phone/img?dealID='+enc.encrypt_key(deal_entity.key())+'&size='+size
		
	return img_url
	
def get_deals_in_area(tags,request_point,precision=5):
	'''
	tags = list of tags that are strings
	request point is db.GeoPt format
	precision is int
	'''
	request_point = levr.geo_converter('42.35,-71.110')
	logging.debug(precision)
	center_hash = geohash.encode(request_point.lat,request_point.lon,precision=precision)
	logging.debug(center_hash)
	hash_set = geohash.expand(center_hash)
	logging.debug(hash_set)
	
	##DEBUG
	ref_query = levr.Deal.all().filter('deal_status =','active')
	for tag in tags:
		if tag != 'all':
			ref_query.filter('tags =',tag)
	ref_deals = ref_query.fetch(None)
	logging.info("total number of deals: "+str(ref_deals.__len__()))
#	for d in ref_deals:
#		logging.debug(d.geo_hash)
	##/DEBUG
	
	
	####build search query
	#only grabbing deal keys, then batch get array
	deal_keys = []
	for query_hash in hash_set:
		#only grab keys for deals that have active status
		q = levr.Deal.all(keys_only=True).filter('deal_status =','active')
		#grab all deals where primary_cat is in tags
		for tag in tags:
			#all is a special keyword
			if tag != 'all':
				logging.debug('tag: '+str(tag))
				q.filter('tags =',tag)
		#filter by geohash
		q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
#					logging.debug(q)
#					logging.debug(levr.log_dict(q.__dict__))
		
		#get all keys for this neighborhood
		fetched_deals = q.fetch(None)
		logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
		
		deal_keys.extend(fetched_deals)
#					logging.debug(deal_keys)
	
	#batch get results. here is where we would set the number of results we want and the offset
	deals = levr.Deal.get(deal_keys)
	return deals
