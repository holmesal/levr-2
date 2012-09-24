import json
import levr_encrypt as enc
import levr_utils
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
		logging.info("EERRRRR")
		#parameter is empty
		if required == True:
			send_error(self,'Required parameter not passed: '+str(parameter_name))
		return False
	else:
		#parameter is not empty
		#if parameter is an entity key, make sure
		if param_type == 'key':
			logging.info('HI')
			#parameter is an entity key
			try:
				logging.info('HEY THERE')
				logging.debug(parameter)
				parameter = enc.decrypt_key(parameter)
				logging.debug(parameter)
				logging.debug('err')
				parameter = db.Key(parameter)
				logging.debug(parameter)
				logging.debug('end')
			except:
				if required == True:
					send_error(self,'Invalid parameter: '+str(parameter_name)+"; "+str(parameter))
				return False
		elif param_type == 'int':
			logging.debug('integer')
			if not parameter.isDigit():
				if required == True:
					send_error(self,'Invalid parameter: '+str(parameter_name)+"; "+str(parameter))
				return False
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
			'largeImg'		: levr_utils.create_img_url(deal,'large'),
			'geoHash'		: deal.geo_hash,
			'geoPoint'		: str(deal.geo_point),
			'redemptions'	: 'TODO!!',
			'smallURL'		: levr_utils.create_img_url(deal,'small'),
			'status'		: deal.deal_status,
			'shareURL'		: levr_utils.create_share_url(deal),
			'tags'			: deal.tags
			}
	return packaged_deal
def package_user(user,privacyLevel='public'):
	'''alias is added by us, first_name and last_name should be added by all other services (foursquare for sure right now)'''
	if user.alias != '':
		alias  = user.alias
	elif user.first_name != '':
		alias = user.first_name + ' ' + user.last_name[0] + '.'
	else:
		alias = 'Clint Eastwood'
	
	packaged_user = {
		'uid'			: str(user.key()),
		'alias'			: alias,
		'dateCreated'	: user.date_created,
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
		'foursquareName': business.foursquare_name
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
	logging.debug(levr_utils.log_dict(reply))
	self.response.out.write(json.dumps(reply))