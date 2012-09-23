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
def check_param(self,parameter,parameter_name,is_key=False):
	#check if parameter sent in params
	#parameter is passed
	logging.info(parameter_name+": "+str(parameter))
	if not parameter:
		logging.info("EERRRRR")
		#parameter is empty
		send_error(self,'Required parameter not passed: '+str(parameter_name))
		return False
	else:
		#parameter is not empty
		#if parameter is an entity key, make sure
		if is_key == True:
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
				send_error(self,'Invalid parameter: '+str(parameter_name))
				return False
			else:
				return True
		else:
			return True

def package_deal(deal,privacyLevel='public'):
	logging.debug(str(deal.geo_point))
	response = {
			'barcode'		: deal.barcode,
			'business'		: {
								'businessID'	: enc.encrypt_key(deal.businessID),
								'businessName'	: deal.business_name,
								'geoPoint'		: str(deal.geo_point)
								,
								'geoHash'		: deal.geo_hash
							},
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
	return response
def package_user(user,privacyLevel='public'):
	'''alias is added by us, first_name and last_name should be added by all other services (foursquare for sure right now)'''
	
	return {'user':'This is a placeholder for the user, which will be packaged later'}
	
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