from gaesessions import get_current_session
import logging
import levr_classes as levr
import levr_encrypt as enc
import base64
from google.appengine.api import urlfetch
import urllib

def login_check(self):
	'''	for merchants ONLY
		check if logged in, and return a the headerdata if so. if not, bounce to the login page'''
	session = get_current_session()
	logging.debug(session)
	if session.has_key('loggedIn') == False or session['loggedIn'] == False:
		#not logged in, bounce to login page
		logging.info('Not logged in. . .Bouncing!')
		self.redirect('/merchants/login')
		
	elif session.has_key('loggedIn') == True and session['loggedIn'] == True:

		uid = session['uid']
		
		logging.info(uid)
		
		headerData = {
			'loggedIn'	: session['loggedIn'],
			'uid'		: enc.decrypt_key(uid),
			'owner_of'	: session['owner_of'],
			'validated'	: session['validated']
			}
		#return user metadata.
		return headerData
	return
	
def validated_check(user):
	'''checks if this user has any linked businesses or not. does not yet return these businesses'''
	
	num_bus = user.businesses.count()
	
	if num_bus > 0:
		return True
	else:
		return False
		
	'''if user.verified_owner = True:
		return True
	else:
		return False'''
		
def create_deal(deal,business,owner):
	'''deal: a deal object
	merchant: the merchant to be set as the owner of the deal'''
	
	#init tags
	tags = []
	#add tags from the merchant
	tags.extend(business.create_tags())
	logging.info(tags)
	#add tags from deal stuff
	tags.extend(levr.tagger(deal.deal_text))
	logging.info(tags)
	tags.extend(levr.tagger(deal.description))
	logging.info(tags)
	
	#add some other miscellaneous information
	deal.origin = 'merchant'
	deal.pin_color	=	'red'
	
	#copy info over from business
	deal.business_name = business.business_name
	deal.geo_point = business.geo_point
	deal.geo_hash = business.geo_hash
	
	
	
	#get businessID - not encrypted - from database
	#businessID = business.key()
	#logging.debug("businessID: "+str(businessID))
	
	#check if the merchant has validated their business. If so, deploy as active. If not, deploy as pending
	if validated_check(owner):
		logging.deug('OKAY')
		#TODO: SET BUSINESS ID
		deal.deal_status='active'
	else:
		logging.debug('FUCK ALL')
		deal.deal_status='pending'
		deal.businessID = owner.owner_of
		
	deal.put()
	logging.info(levr.log_model_props(deal))
	
	#fire off a task to do the image rotation stuff
		task_params = {
			'blob_key'	:	str(img_key)
		}
		taskqueue.add(url='/tasks/checkImageRotationTask',payload=json.dumps(task_params))
	
	
	return deal
	
def call_merchant(business):
	#call the business
	#twilio credentials
	sid = 'AC4880dbd1ff355288728be2c5f5f7406b'
	token = 'ea7cce49e3bb805b04d00f76253f9f2b'
	twiliourl='https://api.twilio.com/2010-04-01/Accounts/AC4880dbd1ff355288728be2c5f5f7406b/Calls.json'
	
	auth_header = 'Basic '+base64.b64encode(sid+':'+token)
	logging.info(auth_header)
	
	request = {'From':'+16173608582',
				'To':'+16052610083',
				'Url':'http://www.levr.com/api/merchant/twilioanswer',
				'StatusCallback':'http://www.levr.com/api/merchant/twiliocallback'}
	
	result = urlfetch.fetch(url=twiliourl,
							payload=urllib.urlencode(request),
							method=urlfetch.POST,
							headers={'Authorization':auth_header})
	
	logging.info(levr.log_dict(result.__dict__))
