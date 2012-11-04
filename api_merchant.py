from google.appengine.api import taskqueue, urlfetch
from google.appengine.ext import blobstore, db
#from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext.webapp import blobstore_handlers
from tasks import IMAGE_ROTATION_TASK_URL
import api_utils
import base64
import json
import levr_classes as levr
import levr_encrypt as enc
import logging
import promotions as promo
import time
import urllib
import webapp2
from datetime import datetime
from datetime import timedelta
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

class ConnectMerchantHandler(api_utils.BaseClass):
	'''
	A handler for creating a merchant account
	'''


	@api_utils.validate(None, 'param',
					email = True,
					pw = True,
					businessName = True,
					vicinity = True,
					ll = True,
					types = True,
					development = False,
					)
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
		user_doesnt_own_business_message = 'User does not own that business'
		# for packaging
		private = True
		followers = False
		
		# input values
		email = kwargs.get('email')
		password = kwargs.get('pw')
		business_name = kwargs.get('businessName')
		vicinity = kwargs.get('vicinity')
		geo_point = kwargs.get('ll')
		types = kwargs.get('types')
		development = kwargs.get('development',True) # TODO: switch this to False by default when changing to live
		phone_number = kwargs.get('phoneNumber','')
		# TODO: accept phone number as well
		try:
			# Convert input data
			password = enc.encrypt_password(password)
			types = types.split(',')
			
			logging.debug('{}\n{}\n{}\n{}'.format(repr(business_name),repr(vicinity),geo_point,repr(types)))
			
			# check for existing entities
			user = levr.Customer.all().filter('email',email).get()
			requested_business = levr.Business.all().filter('business_name',business_name).filter('vicinity',vicinity).get()
			
			if user:
				logging.info('User exists')
				# check password
				assert user.pw == password, 'Password does not match username'
				
				# user should have a business
				try:
					business = user.businesses.get()
					# if the user has a business, it should be the business that was requested
					assert business, 'User does not own any businesses yet'
				except:
					logging.debug('user does not have a business yet - create one')
					# if the user does not have a business yet, add this one.
					business = levr.create_new_business(business_name,vicinity,geo_point,types,phone_number,
													owner=user
													)
#					assert False, user_doesnt_own_business_message
				else:
					logging.debug('User owns a business')
#					logging.debug(levr.log_model_props(business.owner))
#					logging.debug(levr.log_model_props(requested_business.owner))
					if requested_business:
						assert business.key() == requested_business.key(), user_doesnt_own_business_message
				
				
				
			else:
				logging.debug('User does not exist. Create a new one!!')
				# Create an account for the user with that business
				user = levr.create_new_user(
										tester=development,
										pw=password,
										email=email,
										display_name=business_name
										)
				logging.debug(business_name)
				logging.debug(levr.log_model_props(user))
				if not requested_business:
					logging.debug('requested business was not found')
					business = levr.create_new_business(business_name,vicinity,geo_point,types,phone_number,
													owner=user
													)
				else:
					logging.debug('requested business was found')
					business = requested_business
					# 
					business.owner = user
					business.put()
			
			logging.debug('business: '+repr(business))
			#===================================================================
			# # Send message to the founders that someone has signed up for the app
			#===================================================================
			if not development:
				try:
					from google.appengine.api import mail
					message = mail.AdminEmailMessage(
													sender = 'patrick@levr.com',
													subject = 'New Merchant',
													)
					message.body = levr.log_model_props(user,['email','display_name',])
					message.body += levr.log_model_props(business,['business_name','vicinity'])
					message.check_initialized()
					message.send()
					
				except:
					levr.log_error()
			
			#===================================================================
			# # package and send
			#===================================================================
			packaged_user = api_utils.package_user(user, private, followers,send_token=True)
			packaged_business = api_utils.package_business(business)
			response = {
					'user' : packaged_user,
					'business' : packaged_business
					}
			api_utils.send_response(self,response)
			# TODO: Merchant connect - handle all cases - new and existing accounts
		except AssertionError,e:
			api_utils.send_error(self,e.message)
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
class MerchantDealsHandler(api_utils.BaseClass):
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
			deals = api_utils.fetch_all_users_deals(user)
			
			# package deals
			private = True
			packaged_deals = api_utils.package_deal_multi(deals, private)
			
			# return
			response = {
					'deals' : packaged_deals
					}
			self.send_response(response, user)
			
		except Exception,e:
			levr.log_error(e)
			self.send_error()
		
	
class RequestUploadURLHandler(api_utils.BaseClass):
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
	def get(self):
		'''
		A test form to test uploading a deal
		'''
		upload_url = blobstore.create_upload_url(NEW_DEAL_UPLOAD_URL)
		logging.info(upload_url)
		# The method must be "POST" and enctype must be set to "multipart/form-data".
		self.response.out.write('<html><body>')
		self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
		self.response.out.write('''Upload File: <input type="file" name="img"><br>''')
		self.response.out.write('uid: 			<input type="text" name="uid" value="{}"> <br>'.format('tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51StjnMAaChA='))
		self.response.out.write('levrToken: 	<input type="text" name="levrToken" value="{}"> <br>'.format('4QeGPF4WtlUlpG7pKxAXl90LyZGBFT6ECLdvCwPJXDI'))
		self.response.out.write('businessID:	<input type="text" name="businessID" value="{}"> <br>'.format('tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErvitTapPLKLhLS0Ss_1-IaChA='))
		self.response.out.write('description: 	<input type="text" name="description" value="{}"> <br>'.format('description!!!'))
		self.response.out.write('dealText:		<input type="text" name="dealText" value="{}"> <br>'.format('dealText!!!'))
		
		self.response.out.write('<input type="submit"name="submit" value="Create!"> </form></body></html>')
	
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
		img_key = ''
		try:
			
			#===================================================================
			# Assure that an image was uploaded
			#===================================================================
			if self.get_uploads():
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
				upload_flag = True
				
				# send the image to the img rotation task que
				task_params = {
								'blob_key'	:	str(img_key)
								}
				logging.info('Sending this to the img rotation task: '+str(task_params))
				taskqueue.add(url=IMAGE_ROTATION_TASK_URL,payload=json.dumps(task_params))
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
			deal_entity = levr.dealCreate(params, 'phone_merchant', upload_flag)
			
			
			
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
			# Respond with all of the users deals
			#===================================================================
			private = True
			deals = api_utils.fetch_all_users_deals(user)
			packaged_deals = api_utils.package_deal_multi(deals, private)
			
			response = {
					'deals'	: packaged_deals
					}
			
			api_utils.send_response(self,response, user)
			
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
			
class EditDealHandler(blobstore_handlers.BlobstoreUploadHandler):
	'''
	A handler to upload new data for an existing deal in the database
	Will optionally receive an image.
	'''
	def get(self):
		'''
		A test form to test editing a deal
		'''
		upload_url = blobstore.create_upload_url(EDIT_DEAL_UPLOAD_URL)
		logging.info(upload_url)
		# The method must be "POST" and enctype must be set to "multipart/form-data".
		self.response.out.write('<html><body>')
		self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
		self.response.out.write('''Upload File: <input type="file" name="img"><br>''')
		self.response.out.write('uid: 			<input type="text" name="uid" value="{}"> <br>'.format('tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51Stsm8gaChA='))
		self.response.out.write('levrToken: 	<input type="text" name="levrToken" value="{}"> <br>'.format('tFCBPw9A6gt2-Wq6K0RHxYQDkpPUFWvWD-FhCFSQCjM'))
		self.response.out.write('dealID:		<input type="text" name="dealID" value="{}"> <br>'.format('tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fC3GJdErv19TaoeLGNiu51Stsm8gaChDyDrrMSui1aMhOG-0X'))
		self.response.out.write('description: 	<input type="text" name="description" value="{}"> <br>'.format('description!!!'))
		self.response.out.write('dealText:		<input type="text" name="dealText" value="{}"> <br>'.format('dealText!!!'))
		
		self.response.out.write('<input type="submit"name="submit" value="Create!"> </form></body></html>')
	
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
		deal_text = kwargs.get('dealText',None)
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
				old_img_key.delete()
#				BlobInfo.get(old_img_key).delete()
			else:
				assert description or deal_text, 'Thanks for sending me something to update.'
			#===================================================================
			# Update new deal informations
			#===================================================================
			if description:
				deal.description = description
			if deal_text:
				deal.deal_text = deal_text
			
			deal.date_end = datetime.now() + timedelta(days=levr.MERCHANT_DEAL_LENGTH)
			
			
			deal.put()
			
			
			private = True
			deals = api_utils.fetch_all_users_deals(user)
			packaged_deals = api_utils.package_deal_multi(deals, private)
			
			
			response = {
					'deals'	: packaged_deals
					}
			api_utils.send_response(self,response, user)
			
		except AssertionError,e:
			api_utils.send_error(self,e.message)
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')
			
		
class ExpireDealHandler(api_utils.BaseClass):
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
		@rtype: bool
		'''
		user = kwargs.get('actor')
		deal = kwargs.get('deal')
		try:
			# assure that the user is the owner of the deal
			assert deal.parent_key() == user.key(), 'User does not own that deal'
			
			deal.deal_status = 'expired'
			
			# set the deal expiration date to... now!
			deal.date_end = datetime.now()
			
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
		
class ReactivateDealHandler(api_utils.BaseClass):
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
			
			
			# set the date of expiration to the future!
			deal.date_end = datetime.now() + timedelta(days=levr.MERCHANT_DEAL_LENGTH)
			
			
			deal.put()
			
			private = True
			packaged_deal = api_utils.package_deal(deal, private)
			response = {
					'deal'	: packaged_deal
					}
			
			api_utils.send_response(self,response, user)
			
		except AssertionError,e:
			api_utils.send_error(self,e.message)
		except Exception,e:
			api_utils.send_error(self,'Server Error')

class FetchPromotionOptionsHandler(api_utils.BaseClass):
	'''
	A handler for fetching the available promotion options for merchants
	'''
	def get(self,*args,**kwargs):
		try:
			promotions = [promo.PROMOTIONS[key] for key in promo.PROMOTIONS]
			
			
			response = {
					'promotions' : promotions
					}
			
			api_utils.send_response(self,response)
			
		except AssertionError,e:
			api_utils.send_error(self,str(e))
		except Exception,e:
			levr.log_error(e)
			api_utils.send_error(self,'Server Error')



class SetPromotionHandler(api_utils.PromoteDeal):
	'''
	A handler for activating a promotion. Will accept a users information and
		an identifier for a promotion. The types of promotions correspond to the
		identifiers returned in the FetchPromotionOptionsHandler
	'''
	@api_utils.validate(None, 'param',
					user = True,
					levrToken = True,
					promotionID = True,
					deal = True,
					tags = False
					)
	@api_utils.private
	def post(self,*args,**kwargs):
		user = kwargs.get('actor')
		promotion_id = kwargs.get('promotionID')
		deal = kwargs.get('deal')
		self.tags = kwargs.get('tags',[])
#		development = kwargs.get('development')
		
		# init the PromoteDeal class
		logging.debug(type(deal))
		logging.debug(type(user))
		
		
		
		try:
			# init super class
			super(SetPromotionHandler,self).__initialize__(deal,user)
			
			self.run_promotion(promotion_id,tags=self.tags,auto_put=True)
			
#			# promotions can only be applied once
#			assert promotionID not in self.deal.promotions, \
#				'Deal already has promotion: '+promotionID
#			
#			# act accordingly
#			if promotionID == promo.BOOST_RANK:
#				deal = self.boost_rank()
#				
#			elif promotionID == promo.MORE_TAGS:
#				
#				assert tags, 'Required parameter not passed, tags: '+str(tags)
#				deal = self.more_tags(tags)
#				
#			elif promotionID == promo.RADIUS_ALERT:
#				deal = self.radius_alert()
#				
#			elif promotionID == promo.NOTIFY_PREVIOUS_LIKES:
#				deal = self.notify_previous_likes()
#				
#			elif promotionID == promo.NOTIFY_RELATED_LIKES:
#				deal = self.notify_related_likes()
#			else:
#				assert False, 'Did not recognize promotion type.'
#			
			# return success
			response = self.get_all_deals_response()
			api_utils.send_response(self,response, user)
		except AssertionError,e:
			self.send_error(str(e))
		except Exception,e:
			levr.log_error(e)
			self.send_error()
class ConfirmPromotionHandler(api_utils.PromoteDeal):
	@api_utils.validate(None, 'param',
					user = True,
					levrToken = True,
					promotionID = True,
					deal = True,
					receipt = True
					)
	@api_utils.private
	def post(self,*args,**kwargs):
		'''
		A handler to confirm that payment was received for a promotion
		'''
		user = kwargs.get('actor')
		deal = kwargs.get('deal')
		promotion_id = kwargs.get('promotionID')
		receipt = kwargs.get('receipt')
		
		try:
			# init the super class
			super(ConfirmPromotionHandler,self).__initialize__(deal,user)
			# confirm the promotion
			self.confirm_promotion(promotion_id, receipt)
			# return success - send all deals
			response = self.get_all_deals_response()
			self.send_response(response, self.user)
			
		except AssertionError,e:
			self.send_error(e)
			logging.warning(e)
		except Exception,e:
			levr.log_error(e)
			self.send_error()


class CancelPromotionHandler(api_utils.PromoteDeal):
	@api_utils.validate(None, 'param',
					user = True,
					levrToken = True,
					promotionID = True,
					deal = True,
					)
	@api_utils.private
	def post(self,*args,**kwargs):
		user = kwargs.get('actor')
		promotion_id = kwargs.get('promotionID')
		deal = kwargs.get('deal')
#		development = kwargs.get('development')
		try:
			# init super class
			super(CancelPromotionHandler,self).__initialize__(deal,user)
			
			# remove the promotion
			if promotion_id == 'all':
				for p in self.deal.promotions:
					self.remove_promotion(p)
			else:
				self.remove_promotion(promotion_id)
			# send success
			response = self.get_all_deals_response()
			self.send_response(response,self.user)
		except AssertionError,e:
			self.send_error(e)
			logging.warning(e)
		except Exception,e:
			levr.log_error(e)
			self.send_error()
			
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
								('/api/merchant/promote/get',FetchPromotionOptionsHandler),
								('/api/merchant/promote/set',SetPromotionHandler),
								('/api/merchant/promote/confirm',ConfirmPromotionHandler),
								('/api/merchant/promote/cancel',CancelPromotionHandler)
								
								## old...
#								('/api/merchant/initialize', InitializeMerchantHandler),
#								('/api/merchant/call', CallMerchantHandler),
#								('/api/merchant/verify', VerifyMerchantHandler),
#								('/api/merchant/twilioanswer', TwilioAnswerHandler),
#								('/api/merchant/twiliocheckcode', TwilioCheckCodeHandler),
#								('/api/merchant/twiliocallback', TwilioCallbackHandler)
								],debug=True)




