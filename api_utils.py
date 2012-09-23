import json

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


def package_deal(deal,privacyLevel='public'):
	response = {
			'barcode'		: deal.barcode,
			'business'		: {
								'businessID'	: enc.encrypt_key(businessID),
								'businessName'	: deal.business_name,
								'geoPoint'		: deal.geo_point,
								'geoHash'		: deal.geo_hash
							},
			'dateUploaded'	: deal.date_end,
			'dealID'		: enc.encrypt_key(deal.key()),
			'dealText'		: deal.deal_text,
			'description'	: deal.description,
			'isExclusive'	: deal.is_exclusive,
			'largeImg'		: levr_utils.create_img_url(deal,'large'),
			'geoHash'		: deal.geo_hash,
			'geoPoint'		: deal.geo_point,
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
	meta = {'success':True,
			'error':''}
	
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
	self.response.out.write(json.dumps(reply))