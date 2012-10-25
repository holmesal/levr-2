from google.appengine.api import urlfetch
from google.appengine.ext import db
import api_utils
import base64
import levr_classes as levr
import levr_encrypt as enc
import logging
import time
import urllib
import webapp2
#import api_utils_social as social
#from random import randint
#import json


class InitializeMerchantHandler(webapp2.RequestHandler):
	def post(self):
		#curl --data 'businessName=alonsostestbusiness&vicinity=testVicinity&phone=%2B16052610083&geoPoint=-71.234,43.2345' http://www.levr.com/api/merchant/initialize | python -mjson.tool
		
		'''REMEMBER PHONE NUMBER FORMATTING STUFF'''
		api_utils.send_error(self,'Hey ethan. Ask alonso about the formatting of the phone number.')
		return
		
		#Grab incoming merchant data
		business_name = self.request.get('businessName')
		if business_name == '':
			api_utils.send_error(self,'Required parameter not passed: businessName')
			return
		vicinity = self.request.get('vicinity')
		if vicinity == '':
			api_utils.send_error(self,'Required parameter not passed: vicinity')
			return
		phone = self.request.get('phone')
		if phone == '':
			api_utils.send_error(self,'Required parameter not passed: phone')
			return
		geo_point = self.request.get('geoPoint')
		if geo_point == '':
			api_utils.send_error(self,'Required parameter not passed: geo_point')
			return
		
		#check if business entity already exists based on phone number
		business = levr.Business.gql('WHERE business_name = :1 AND phone = :2',business_name,phone).get()
		
		
		if business:
			#if a business has been created and an owner has been set, return an error
			if business.owner:
				logging.info('Owner is set!')
				api_utils.send_error(self,'That business has already been verified. If you need help, email support@levr.com')
				return
			#if a business has been created but no owner has been set, return the business
		else:
			logging.debug('Creating a new business.')
			#create a new business entity with no owner
			business = levr.Business()
			business.business_name = business_name
			business.vicinity = vicinity
			business.phone = phone
			business.geo_point = levr.geo_converter(geo_point)
			business.activation_code = str(int(time.time()))[-4:]
			#put
			business.put()
		
		#reply with business object
		response = {'business':api_utils.package_business(business)}
		api_utils.send_response(self,response)

class CallMerchantHandler(webapp2.RequestHandler):
	def get(self):
		
		businessID = self.request.get('businessID')
		if businessID == '':
			api_utils.send_error(self,'Required parameter not passed: businessID')
			return
		#decrypt uid
		try:
			businessID = db.Key(enc.decrypt_key(businessID))
		except:
			api_utils.send_error(self,'Invalid parameter: businessID')
			return
		#grab the business
#		business = levr.Business.get(businessID)
		
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
		
		#self.response.out.write('Calling business with id: ')

class VerifyMerchantHandler(webapp2.RequestHandler):
	def get(self):
		
		#check code
		pass
		# if legit:
		#create user entity and make the owner of the business
		
class TwilioAnswerHandler(webapp2.RequestHandler):
	def post(self):
		self.response.out.write('''<?xml version="1.0" encoding="UTF-8"?>
		<Response>
			<Gather timeout="10" finishOnKey="*" action="http://www.levr.com/api/merchant/twiliocheckcode">
				<Say>Thanks for using Levr!</Say>
				<Say>Please enter your activation code and then press star.</Say>
			</Gather>
		</Response>''')
		
class TwilioStatus
		
class TwilioCheckCodeHandler(webapp2.RequestHandler):
	def post(self):
		logging.debug(self.request.body)
		code = self.request.get('Digits')
		callto = self.request.get('To')
		
		logging.debug(code)
		logging.debug(callto)
		
		business = levr.Business.gql('WHERE phone=:1 AND activation_code=:2',callto,code).get()
		
		if business:
			logging.debug('Business found')
			logging.debug(business)
			self.response.out.write('''<?xml version="1.0" encoding="UTF-8"?>
		<Response>
			<Say>Your account has been activated. Goodbye.</Say>
			<Hangup/>
		</Response>''')
		else:
			logging.debug('Business NOT found')
			'''THIS ISN'T WORKING PROPERLY - A SECOND CALL IS INITIATED WHEN INCORRECT PIN IS ENTERED'''
			self.response.out.write('''<?xml version="1.0" encoding="UTF-8"?>
		<Response>
			<Gather timeout="10" finishOnKey="*" action="http://www.levr.com/api/merchant/twiliocheckcode">
				<Say>That code doesn't look right. Could you try again?</Say>
				<Say>Please enter your activation code and then press star.</Say>
			</Gather>
			<Hangup/>
		</Response>''')
		
		
class TwilioCallbackHandler(webapp2.RequestHandler):
	def post(self):
		pass

		
app = webapp2.WSGIApplication([('/api/merchant/initialize', InitializeMerchantHandler),
								('/api/merchant/call', CallMerchantHandler),
								('/api/merchant/verify', VerifyMerchantHandler),
								('/api/merchant/twilioanswer', TwilioAnswerHandler),
								('/api/merchant/twiliocheckcode', TwilioCheckCodeHandler),
								('/api/merchant/twiliocallback', TwilioCallbackHandler)],debug=True)