from google.appengine.api import taskqueue, urlfetch
from google.appengine.ext import blobstore, db
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext.webapp import blobstore_handlers
from tasks import IMAGE_ROTATION_TASK_URL
import api_utils
import base64
import json
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




#===============================================================================
# SOME NEW AGE MERCHANT SHIT!!
#===============================================================================
# TODO: make some unit tests for this

class ConnectMerchantHandler(webapp2.RequestHandler):
	'''
	A handler for creating a merchant account
	'''


	@api_utils.validate(None, 'param',
					email = True,
					password = True,
					businessName = True,
					vicinity = True,
					geoPoint = True,
					types = True,
					development = False,
					)
	@api_utils.private
	def post(self,*args,**kwargs):
		'''
		Checks for existing account with that business
		If the account exists, return true
		
		@attention: Only handles the case where a single account is tied to no more than one business
		
		@keyword email: required
		@keyword password: required
		@keyword business_name: required
		@keyword vicinity: required
		@keyword geo_point: required
		@keyword types: require
		@keyword development: optional
		
		@return: packaged_user with levrToken, packaged_business
		'''
		# for invalid credential responses
		user_doesnt_own_business = 'User does not own that business'
		# for packaging
		private = True
		followers = False
		
		# input values
		email = kwargs.get('email')
		password = kwargs.get('password')
		business_name = kwargs.get('business_name')
		vicinity = kwargs.get('vicinity')
		geo_point = kwargs.get('geo_point')
		types = kwargs.get('types')
		development = kwargs.get('development')
		try:
			user = levr.Customer.all().filter('email',email).get()
			requested_business = levr.Business.all().filter('business_name',business_name).filter('vicinity',vicinity).get()
			if user:
				# check password
				password = enc.encrypt_password(password)
				assert user.pw == password, 'Password does not match username'
				
				# user should have a business
				try:
					business = user.businesses.get()
				except:
					# if the 
					assert False, user_doesnt_own_business
				
				# if the user has a business, it should be the business that was requested
				assert business == requested_business, user_doesnt_own_business
				
				
			else:
				# Create an account for the user with that business
				user = levr.create_new_user(tester=development)
				if not requested_business:
					business = levr.create_new_business(business_name,vicinity,geo_point,types,owner=user,development=development)
				else:
					business = requested_business
					# 
					business.owner = user
					business.put()
			# package and send
			packaged_user = api_utils.package_user(user, private, followers,send_token=True)
			packaged_business = api_utils.package_business(business)
			response = {
					'user' : packaged_user,
					'business' : packaged_business
					}
			api_utils.send_response(self,response)
			# TODO: Merchant connect - handle all cases - new and existing accounts
		except AssertionError,e:
			api_utils.send_error(self,e)
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
		# TODO: add a property to customer that says whether or not the user is merchant
		# TODO: send the founders a notification when a business signs up
class MerchantDealsHandler(webapp2.RequestHandler):
	'''
	A handler for serving all of a merchants deals for their manage page
	'''
	@api_utils.validate(None, 'param',
					user = True,
					levrToken = True
					)
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		@keyword actor:
		
		@return: array of deal objects
		'''
		user = kwargs.get('actor')
		try:
			deals = levr.Deal.all().ancestor(user).fetch(None)
			
			# Sort the deals
			creation_dates = [deal.get('date_created') for deal in deals]
			
			toop = creation_dates,deals
			sorted_toop = sorted(toop)
			sorted_dates,sorted_deals = zip(*sorted_toop) #@UnusedVariable: sorted_dates
			
			# package and send
			private = True
			packaged_deals = api_utils.package_deal_multi(sorted_deals, private)
			
			response = {
					'deals' : packaged_deals
					}
			api_utils.send_response(self,response, user)
			
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
class RequestUploadURLHandler(webapp2.RequestHandler):
	'''
	A handler to serve an upload url for uploading an image to the server
	'''
	@api_utils.validate(None, 'param',
					user = True,
					levrToken = True,
					action = True,
					)
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		@keyword actor: 
		@keyword action: if the deal will be a new deal or if it will be edited
		
		@return: url
		@rtype: string
		'''
		user = kwargs.get('actor')
		action = kwargs.get('action')
		try:
			if action == 'add':
				upload_url = blobstore.create_upload_url(NEW_DEAL_UPLOAD_URL)
			elif action == 'edit':
				upload_url = blobstore.create_upload_url(EDIT_DEAL_UPLOAD_URL)
			else:
				raise KeyError('Action not recognized: '+str(action))
			
			response  = {
						'uploadURL' : upload_url
						}
			
			api_utils.send_response(self,response,user)
			
		except KeyError,e:
			api_utils.send_error(self,e)
		except Exception,e:
			api_utils.send_error(self,'Server Error')

class AddNewDealHandler(blobstore_handlers.BlobstoreUploadHandler):
	'''
	A handler to upload a NEW deal to the database
	'''
	@api_utils.validate(None, 'param',
					user = True,
					levrToken = True,
					business = True,
					description = True,
					dealText = True,
					)
	def post(self,*args,**kwargs):
		'''
		@keyword actor: required
		@keyword business: required
		@keyword description: required
		@keyword deal_text: required
		@keyword development: required
		
		@requires: an image is uploaded - need the blob_key
		
		@return: the newly created deal object
		@rtype: dict
		'''
		user = kwargs.get('actor')
		business = kwargs.get('business')
		description = kwargs.get('description')
		deal_text = kwargs.get('dealText')
		development = kwargs.get('development')
		try:
			
			#===================================================================
			# Assure that an image was uploaded
			#===================================================================
			if self.get_uploads():
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
				upload_flag = True
			else:
				upload_flag = False
				raise KeyError('Image was not uploaded')
			
			#===================================================================
			# Assemble the deal parameters! And create the deal!!
			#===================================================================
			params = {
					'user'				: user,
					'uid'				: user.key(),
					'business'			: business,
					'deal_description'	: description,
					'deal_line1'		: deal_text,
					'development'		: development,
					'img_key'			: img_key
					}
			
			#TODO: add this case to the create_deal function
			deal_entity = levr.dealCreate(params, 'phone_merchant', upload_flag,expires='never')
			
			
			
			#===================================================================
			# Send deal to the task param to rotate the image if it needs to be
			#===================================================================
			task_params = {
						'blob_key'	: str(deal_entity.img.key())
						}
			taskqueue.add(url = IMAGE_ROTATION_TASK_URL, payload = json.dumps(task_params))
			
			#===================================================================
			# Aw hell.. why not give them some karma too.
			#===================================================================
			user.karma += 5
			# no need to level_check on them though...
			user.put()
			
			#===================================================================
			# Create some nifty notifications
			#===================================================================
			try:
				levr.create_notification('followedUpload',user.followers,user.key(),deal_entity)
			except:
				levr.log_error()
			
			#===================================================================
			# Respond
			#===================================================================
			private = True
			packaged_deal = api_utils.package_deal(deal_entity, private)
			
			response = {
					'deal'	: packaged_deal
					}
			
			api_utils.send_response(self,response, user)
			
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
			
class EditDealHandler(blobstore_handlers.BlobstoreDownloadHandler):
	'''
	A handler to upload new data for an existing deal in the database
	Will optionally receive an image.
	'''
	@api_utils.validate(None, 'param',
					user = True,
					deal = True,
					levrToken = True,
					description = False,
					dealText = False,
					)
	@api_utils.private
	def post(self,*args,**kwargs):
		'''
		@keyword actor: required
		@keyword deal: required
		@keyword description: optional
		@keyword dealText: optional
		
		@var new_img_key: optional - the blob key of the uploaded image
		
		@return: the new deal object
		@rtype: dict
		'''
		user = kwargs.get('actor')
		deal = kwargs.get('deal')
		description = kwargs.get('description',None)
		deal_text = kwargs.get('deal_text',None)
		try:
			# assure that the user is the owner of the deal
			assert deal.parent_key() == user.key(), 'User does not own that deal'
			
			#===================================================================
			# Check for image upload
			#===================================================================
			if self.get_uploads():
				new_img_key	= self.get_uploads()[0].key()
				# grab old key so we can delete it
				old_img_key = deal.img
				# replace with new key
				deal.img = new_img_key
				
				# delete that old key
				BlobInfo.get(old_img_key).delete()
			else:
				assert description or deal_text, 'Are you trying to edit the deal or what? Send me something to update.'
			#===================================================================
			# Update new deal informations
			#===================================================================
			if description:
				deal.description = description
			if deal_text:
				deal.deal_text = deal_text
			
			deal.put()
			
			private = True
			packaged_deal = api_utils.package_deal(deal, private)
			response = {
					'deal'	: packaged_deal
					}
			api_utils.send_response(response, user)
			
		except AssertionError,e:
			api_utils.send_error(self,e)
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
		
class ExpireDealHandler(webapp2.RequestHandler):
	'''
	A handler to expire a deal from a merchant
	'''
	@api_utils.validate(None,'param',
					user = True,
					levrToken = True,
					deal = True
					)
	def post(self,*args,**kwargs):
		'''
		@keyword actor: 
		@keyword deal: 
		
		@requires: user is the owner of the deal
		
		@return: Success
		@rtype: Boolean
		'''
		user = kwargs.get('actor')
		deal = kwargs.get('deal')
		try:
			# assure that the user is the owner of the deal
			assert deal.parent_key() == user.key(), 'User does not own that deal'
			
			deal.deal_status = 'expired'
			
			deal.put()
			
			private = True
			packaged_deal = api_utils.package_deal(deal, private)
			
			response = {
					'deal'	: packaged_deal
					}
			
			api_utils.send_response(self,response, user)
			
		except AssertionError,e:
			api_utils.send_error(self,e)
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
		
class ReactivateDealHandler(webapp2.RequestHandler):
	'''
	A handler to set a deal as active
	'''
	@api_utils.validate(None,'param',
					user = True,
					levrToken = True,
					deal = True,
					)
	def post(self,*args,**kwargs):
		'''
		@keyword actor: required
		@keyword deal: required
		@keyword development: required
		@requires: user is the owner of the deal
		
		@return: success
		@rtype: Boolean
		'''
		user = kwargs.get('actor')
		deal = kwargs.get('deal')
		development = kwargs.get('development')
		
		try:
			#assure that this user does own the deal
			assert deal.parent_key() == user.key()
			
			if development:
				deal.deal_status = 'test'
			else:
				deal.deal_status = 'active'
			
			deal.put()
			
			private = True
			packaged_deal = api_utils.package_deal(deal, private)
			response = {
					'deal'	: packaged_deal
					}
			
			api_utils.send_response(response, user)
			
		except AssertionError,e:
			api_utils.send_error(self,e)

# Quality Assurance for generating the upload urls
NEW_DEAL_UPLOAD_URL = '/api/merchant/upload/add'
EDIT_DEAL_UPLOAD_URL = '/api/merchant/upload/edit'
app = webapp2.WSGIApplication([
								('/api/merchant/connect',ConnectMerchantHandler),
								('/api/merchant/deals',MerchantDealsHandler),
								('/api/merchant/upload/request',RequestUploadURLHandler),
								(NEW_DEAL_UPLOAD_URL,AddNewDealHandler),
								(EDIT_DEAL_UPLOAD_URL,EditDealHandler),
								('/api/merchant/remove',ExpireDealHandler),
								('/api/merchant/reactivate',ReactivateDealHandler),
								##
								('/api/merchant/initialize', InitializeMerchantHandler),
								('/api/merchant/call', CallMerchantHandler),
								('/api/merchant/verify', VerifyMerchantHandler),
								('/api/merchant/twilioanswer', TwilioAnswerHandler),
								('/api/merchant/twiliocheckcode', TwilioCheckCodeHandler),
								('/api/merchant/twiliocallback', TwilioCallbackHandler)
								],debug=True)




