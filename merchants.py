#  @PydevCodeAnalysisIgnore
from gaesessions import get_current_session
from google.appengine.api import mail, taskqueue, images, files
from google.appengine.ext import blobstore, db
from google.appengine.ext.webapp import blobstore_handlers
import api_utils
import geo.geohash as geohash
import jinja2
import json
import levr_classes as levr
import levr_encrypt as enc
import logging
import merchant_utils
import os
import time
import webapp2
import mixpanel_track as mp_track

#New alonso additions
import re
from google.appengine.api import urlfetch
import urllib
#import json
#from levr_encrypt import encrypt_key
#from google.appengine.ext import db
#from google.appengine.api import images
#from datetime import datetime
#from datetime import timedelta


jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
class MobileLandingHandler(webapp2.RequestHandler):
	def get(self):
		#check if the merchant is logged in
		session = get_current_session()
		if session.has_key('loggedIn') == True and session['loggedIn'] == True:
			self.redirect("/merchants/mobile/manage")
		else:
			
			template_values = {
				"title"		:	"Welcome to Levr.",
				"title_link":	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-landing.html')
			self.response.out.write(template.render(template_values))

class MobileLoginHandler(webapp2.RequestHandler):
	def get(self):
		#check if the merchant is logged in
		session = get_current_session()
		if session.has_key('loggedIn') == True and session['loggedIn'] == True:
			self.redirect("/merchants/mobile/manage")
		else:
			
			template_values = {
				"title"		:	"Welcome back.",
				"back_link"	:	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-login.html')
			self.response.out.write(template.render(template_values))
	def post(self):
		o_email = self.request.get('email')
		email = o_email.lower()
		pw = enc.encrypt_password(self.request.get('pw'))
		
		user = levr.Customer.gql('WHERE email=:1 AND pw=:2',email,pw).get()
		
		if email == "":
			error = "Please enter your email"
		elif pw == "":
			error = "Please enter your password"
		elif not user:
			error = "Incorrect email or password"
		else:
			error = None
		
		if error:
			template_values = {
				"email"		:	o_email,
				"pw"		:	pw,
				"error"		:	error,
				"title"		:	"Welcome back.",
				"back_link"	:	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-login.html')
			self.response.out.write(template.render(template_values))
			
		else:
			#logged in, start a session and all that jazz
			session = get_current_session()
			session['uid'] = enc.encrypt_key(user.key())
			session['loggedIn'] = True
			session['owner_of']	=	enc.encrypt_key(user.owner_of)
			
			#send to the merchants page
			self.redirect('/merchants/mobile/manage')
			
class MobileLogoutHandler(webapp2.RequestHandler):
	def get(self):
		session = get_current_session()
		session['loggedIn'] = False
		
		self.redirect('/merchants/mobile')
			
class MobileBusinessSelectHandler(webapp2.RequestHandler):
	def get(self):
		#check if the merchant is logged in
		session = get_current_session()
		if session.has_key('loggedIn') == True and session['loggedIn'] == True:
			self.redirect("/merchants/mobile/manage")
		else:
			
			#grab the query input if it's there
			query = self.request.get('query')
			
			template_values = {
				"title"		:	"Find your business.",
				"query"		:	query,
				"back_link"	:	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-business-select.html')
			self.response.out.write(template.render(template_values))
			
class MobileAutocompleteHandler(webapp2.RequestHandler):
	def get(self):
		query = self.request.get('query')
		
		url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?sensor=false&key=AIzaSyCjddKUEHrVcCDqA9fqLMPUBXH0mrWPpgI&types=establishment&input='+urllib.quote(query)
		
		response = urlfetch.fetch(url)
		
		#if response.status_code == 200:
		logging.debug(response.content)
		reply = json.loads(response.content)
		
		predictions = reply['predictions']
		
		
		self.response.out.write(json.dumps(predictions))
				
		#else:
		#	api_utils.send_error(self,'There was an error finding your business. Please try again later.')
		
		
class MobileBusinessDetailsHandler(webapp2.RequestHandler):
	def get(self):
		try:
			reference = self.request.get('reference')
			query = self.request.get('query')
			
			url = 'https://maps.googleapis.com/maps/api/place/details/json?sensor=false&key=AIzaSyCjddKUEHrVcCDqA9fqLMPUBXH0mrWPpgI&types=establishment&reference='+reference
			
			response = urlfetch.fetch(url)
			reply = json.loads(response.content)
			logging.debug(reply)
			deets = reply['result']
			
			template_values = {
				"vicinity"	:	deets["vicinity"],
				"phone"		:	deets["formatted_phone_number"],
				"name"		:	deets["name"],
				"lat"		:	deets["geometry"]["location"]["lat"],
				"lon"		:	deets["geometry"]["location"]["lng"],
				"reference"	:	reference,
				"query"		:	query,
				"title"		:	"Is this you?",
				"back_link"	:	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-business-details.html')
			self.response.out.write(template.render(template_values))
		
		except:
			levr.log_error(self)

class MobileSignupHandler(webapp2.RequestHandler):
	def get(self):
		#check if the merchant is logged in
		session = get_current_session()
		if session.has_key('loggedIn') == True and session['loggedIn'] == True:
			self.redirect("/merchants/mobile/manage")
		else:
			
			reference = self.request.get('reference')
			
			template_values = {
				"title"		:	"Sign up.",
				"reference":	reference,
				"back_link"	:	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-signup.html')
			self.response.out.write(template.render(template_values))
	def post(self):
		#grab le inputs
		logging.info(self.request.body)
		o_email = self.request.get('email')
		email = o_email.lower()
		pw1 = self.request.get('pw1')
		pw2 = self.request.get('pw2')
		reference = self.request.get('reference')
		
		logging.info(pw1)
		logging.info(pw2)
		logging.info(o_email)
		logging.info(email)
		
		#email regex
		email_regex = re.compile(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")
		
		#email db check
		existing_user = levr.Customer.gql('WHERE email=:1',email).get()
		
		#error-check
		if email=="":
			error = "Please enter an email"
		elif email_regex.match(email) == None:
			error = "Please enter a valid email address"
		elif existing_user:
			error = "That email already exists"
		elif pw1=="":
			error = "Please enter a password"
		elif pw2=="":
			error = "Please confirm your password"
		elif pw1!=pw2:
			error = "Passwords didn't match."
			pw1=""
			pw2=""
		else:
			error = None
		
		if error:
			template_values = {
				"email"		:	o_email,
				"pw1"		:	pw1,
				"pw2"		:	pw2,
				"reference"	:	reference,
				"error"		:	error,
				"title"		:	"Sign up.",
				"back_link"	:	"/merchants/mobile"
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-signup.html')
			self.response.out.write(template.render(template_values))
		
		else:
			#grab the business from google places
			url = 'https://maps.googleapis.com/maps/api/place/details/json?sensor=false&key=AIzaSyCjddKUEHrVcCDqA9fqLMPUBXH0mrWPpgI&types=establishment&reference='+reference
			response = urlfetch.fetch(url)
			reply = json.loads(response.content)
			logging.debug(reply)
			deets = reply['result']
			
			#pull out the business information
			business_name 	= deets["name"]
			phone			= deets["formatted_phone_number"]
			vicinity		= deets["vicinity"]
			geo_point		= db.GeoPt(lat=deets["geometry"]["location"]["lat"],lon=deets["geometry"]["location"]["lng"])
			types			= deets["types"]
			
			#check if that business already exists
			business = levr.Business.all().filter('business_name =', business_name).filter('vicinity =',vicinity).get()
			
			if not business:
				logging.info('business does not exist...creating')
				#create the business
				business = levr.Business(
						business_name=business_name,
						geo_point = geo_point,
						geo_hash = geohash.encode(geo_point.lat,geo_point.lon),
						vicinity = vicinity,
						types = types,
						phone = phone
				)
				
				business.put()
			
			else:
				logging.info('business already exists... pulling')
				#even if there is a business, grab it and update it if the phone number is null
				if not business.phone:
					business.phone = self.request.get('phone')
					business.put()
					
			#at this point, a business should exist
			logging.debug(levr.log_model_props(business))	
			
			#create the owner
			owner = levr.Customer(
				email=email.lower(),
				pw=enc.encrypt_password(pw1),
				owner_of=str(business.key()),
				levr_token=levr.create_levr_token(),
				display_name=business.business_name,
				alias=business.business_name
			)
			
			owner.put()
			
			logging.debug(levr.log_model_props(owner))
			
			#log the owner in
			session = get_current_session()
			session['uid']	= enc.encrypt_key(str(owner.key()))
			session['loggedIn']	= True
			session['validated']= False
			session['owner_of']	=	enc.encrypt_key(owner.owner_of)
			logging.debug(session)
			
			self.redirect('/merchants/mobile/manage')

class MobileManageHandler(webapp2.RequestHandler):
	def get(self):
		
		meta = merchant_utils.login_check_mobile(self)
		
		owner = levr.Customer.get(meta['uid'])
		
		#grab the deals
		q_deals = levr.Deal.gql('WHERE ANCESTOR IS :1 ORDER BY date_created DESC',owner.key())
		logging.info(q_deals.count())
		#package
		deals = []
		active = []
		pending = []
		expired = []
		for deal in q_deals:
			deal.enc_key = enc.encrypt_key(deal.key())
			logging.info(deal.deal_status)
			if deal.deal_status == 'active':
				active.append(deal)
				logging.info('appended to active')
			elif deal.deal_status == 'pending':
				pending.append(deal)
				logging.info('appended to pending')
			elif deal.deal_status == 'expired':
				expired.append(deal)
				logging.info('appended to expired')
		
		deals = active + pending + expired
		logging.info(deals)
		
		
		template_values = {
			"title"		:	"Manage your offers",
			"deals"		:	deals
		}
		
		template = jinja_environment.get_template('templates/merchants-mobile-manage.html')
		self.response.out.write(template.render(template_values))
		
class MobileDealViewHandler(webapp2.RequestHandler):
	def get(self):
		meta = merchant_utils.login_check_mobile(self)
		
		dealID = self.request.get('dealID')
		
		deal = levr.Deal.get(enc.decrypt_key(dealID))
		
		enc_key = enc.encrypt_key(deal.key())
		
		template_values = {
			"title"		:	"This offer is "+deal.deal_status+'.',
			"back_link"	:	'/merchants/mobile/manage',
			"existing_img"	: '/api/deal/'+enc_key+'/img?size=large',
			"deal"		:	deal,
			"enc_key"	:	enc_key
		}
		
		template = jinja_environment.get_template('templates/merchants-mobile-deal-view.html')
		self.response.out.write(template.render(template_values))
		
class MobileDealHandler(webapp2.RequestHandler):
	def get(self):
		meta = merchant_utils.login_check_mobile(self)
		
		dealID = self.request.get('dealID')
		logging.info(dealID)
		
		if dealID !="":
			#edit
			deal = levr.Deal.get(enc.decrypt_key(dealID))
			enc_key = enc.encrypt_key(deal.key())
			existing_img = api_utils.create_img_url(deal,'large')
			
			template_values = {
				"upload_url"	: blobstore.create_upload_url('/merchants/mobile/deal/edit'),
				"preview_url"	: blobstore.create_upload_url('/merchants/mobile/deal/photorotate'),
				"title"			: "",
				"existing_img"	: '/api/deal/'+enc_key+'/img?size=large',
				"dealID"		: dealID,	#encrypted woohoo
				"deal_text"		: deal.deal_text,
				"description"	: deal.description,
				"deal"			: deal
			}
		else:
			template_values = {
				"upload_url"	: blobstore.create_upload_url('/merchants/mobile/deal/create'),
				"preview_url"	: blobstore.create_upload_url('/merchants/mobile/deal/photorotate'),
				"title"			: ""
			}
		
		logging.info(template_values)
		template = jinja_environment.get_template('templates/merchants-mobile-deal.html')
		self.response.out.write(template.render(template_values))
			
class MobileDealCreateHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		# TODO: combine this
		meta = merchant_utils.login_check_mobile(self)
		uid = meta['uid']
		user = levr.Customer.get(uid)
		
		deal_text = self.request.get('deal_text')
		description = self.request.get("description")
		img_key = blobstore.BlobInfo(blobstore.BlobKey(self.request.get("img_key")))

		# if self.get_uploads(): #will this work?
# 			upload	= self.get_uploads()[0]
# 			blob_key= upload.key()
# 			img_key = blob_key
# 			upload_flag = True
# 		else:
# 			upload_flag = False
# 			raise KeyError('Image was not uploaded')
			
		#initialize the deal - just the stuff from the input here
		deal = levr.Deal(
			img				=	img_key,
			deal_text		=	deal_text,
			description		=	description,
			parent			=	user.key()
		)
		
		#add all the properties from the business
		business = levr.Business.get(user.owner_of)
		logging.info(levr.log_model_props(business))
		
		#kick over to create_deal to finish the deal creation
		deal = merchant_utils.create_deal(deal,business,user)
		
		self.redirect('/merchants/mobile/manage')

class MobileDealEditHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		
		dealID = self.request.get('dealID')
		deal_text = self.request.get('deal_text')
		description = self.request.get('description')
		img_key = self.request.get('img_key')
		
		logging.info(img_key)
		
		
		deal = levr.Deal.get(enc.decrypt_key(dealID))
		
		logging.info(str(deal.img))
		
		deal.deal_text = deal_text
		deal.description = description
		
		if img_key !="":
			img_key = blobstore.BlobInfo(blobstore.BlobKey(img_key))
			deal.img = img_key
			logging.info('IMAGE KEY UPDATED')
			logging.info(str(deal.img))
		
		# if self.get_uploads(): #will this work?
# 			logging.info('IMAGE UPLOADED')
# 			upload	= self.get_uploads()[0]
# 			blob_key= upload.key()
# 			img_key = blob_key
# 			deal.img = img_key
# 		else:
# 			logging.info('NO IMAGE UPLOADED')
		
		deal.put()
		
		self.redirect('/merchants/mobile/manage')
		
class MobilePhotoRotateHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		dealID = self.request.get('dealID')
		logging.info(dealID)
		
		if self.get_uploads(): #will this work?
			logging.info('IMAGE UPLOADED')
			upload	= self.get_uploads()[0]
			blob_key= upload.key()
			
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
					else:
						img.rotate(0)
				
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
					blob_key = files.blobstore.get_blob_key(overwrite)
					
					logging.info('GOT NEW BLOB KEY')
					
			logging.info(blob_key)
			serving_url = '/merchants/mobile/deal/photoserve/'+str(blob_key)
			logging.info(serving_url)

		else:
			upload_flag = False
			raise KeyError('Image was not uploaded')
			
		
		
		if dealID !="":
			#edit
			deal = levr.Deal.get(enc.decrypt_key(dealID))
			existing_img = api_utils.create_img_url(deal,'large')
			
			logging.info('EDIT WAS CALLED')
			
			template_values = {
				"upload_url"	: blobstore.create_upload_url('/merchants/mobile/deal/edit'),
				"preview_url"	: blobstore.create_upload_url('/merchants/mobile/deal/photorotate'),
				"title"			: "",
				"existing_img"	: serving_url,
				"img_key"		: str(blob_key),
				"dealID"		: dealID,	#encrypted woohoo
				"deal_text"		: deal.deal_text,
				"description"	: deal.description
			}
		else:
			
			logging.info('EDIT WAS NOT CALLED')
			
			template_values = {
				"upload_url"	: blobstore.create_upload_url('/merchants/mobile/deal/create'),
				"preview_url"	: blobstore.create_upload_url('/merchants/mobile/deal/photorotate'),
				"existing_img"	: serving_url,
				"img_key"		: str(blob_key),
				"title"			: ""
			}
			
		template = jinja_environment.get_template('templates/merchants-mobile-deal.html')
		self.response.out.write(template.render(template_values))
		
		
class MobilePhotoServeHandler(webapp2.RequestHandler):
	def get(self,*args):
		blob_key = blobstore.BlobInfo.get(blobstore.BlobKey(args[0]))
		#self.send_blob(blob_info)
		logging.info(blob_key)
		blob_data = blob_key.open().read()
		
		logging.info('Blob size: '+str(blob_key.size))
		
		#pass blob data to the image handler
		img			= images.Image(blob_data)
		#get img dimensions
		img_width	= img.width
		img_height	= img.height
		logging.debug(img_width)
		logging.debug(img_height)
		
		aspect_ratio 	= 1. 	#width/height
		output_width 	= 640.	#arbitrary standard
		
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
		logging.info(str(self.response.headers))


class MobileDealExpireHandler(webapp2.RequestHandler):
	def get(self):
		meta = merchant_utils.login_check_mobile(self)
		
		dealID = self.request.get('dealID')
		
		deal = levr.Deal.get(enc.decrypt_key(dealID))
		
#		deal.deal_status = 'expired'
		
		deal.expire()
		
		deal.put()
		
		self.redirect('/merchants/mobile/manage')
		
class MobileDealReanimateHandler(webapp2.RequestHandler):
	def get(self):
		meta = merchant_utils.login_check_mobile(self)
		
		dealID = self.request.get('dealID')
		
		deal = levr.Deal.get(enc.decrypt_key(dealID))
		# TODO: set deal status to active via deal.reactivate
#		deal.deal_status = 'active'
		deal.reanimate()
		deal.put()
		
		self.redirect('/merchants/mobile/manage')


class MobilePhotoHandler(webapp2.RequestHandler):
	def get(self):
		meta = merchant_utils.login_check_mobile(self)
		
		dealID = self.request.get('dealID')
		
		if dealID != "":
			#edit
			deal = levr.Deal.get(enc.decrypt_key(dealID))
			existing_img = api_utils.create_img_url(deal,'large')
			
			template_values = {
				"upload_url"	: blobstore.create_upload_url('/merchants/mobile/photo/edit'),
				"title"			: "Take a photo",
				"existing_img"	: existing_img,
				"dealID"		: dealID			
			}
		else:
			template_values = {
				"upload_url"	: blobstore.create_upload_url('/merchants/mobile/photo/create'),
				"title"			: "Take a photo"		
			}
		
		
		template = jinja_environment.get_template('templates/merchants-mobile-photo.html')
		self.response.out.write(template.render(template_values))
		
class MobilePhotoCreateHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		
		if self.get_uploads(): #will this work?
			upload	= self.get_uploads()[0]
			blob_key= upload.key()
			img_key = blob_key
			upload_flag = True
		else:
			upload_flag = False
			raise KeyError('Image was not uploaded')
				
		logging.info(img_key)
		
		template_values = {
			"img_key"		: img_key,
			"title"			: "Describe your offer"		
		}
		
		template = jinja_environment.get_template('templates/merchants-mobile-dealtext.html')
		self.response.out.write(template.render(template_values))

class MobilePhotoEditHandler(webapp2.RequestHandler):		
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		dealID = self.request.get('dealID')
		edited = self.request.get('edited')
		
		deal = levr.Deal.get(enc.decrypt_key(dealID))
		
		if self.get_uploads(): #will this work?
			upload	= self.get_uploads()[0]
			blob_key= upload.key()
			img_key = blob_key
			upload_flag = True
		else:
			upload_flag = False
		
		if upload_flag == True:
			old_blob = deal.img
			deal.img = img_key
			old.blob.delete()
		
		deal.put()
		
		template_values = {
			"title"		:	"Describe your offer"
		}
		
		template = jinja_environment.get_template('templates/merchants-mobile-dealtext.html')
		self.response.out.write(template.render(template_values))

class MobileDealTextCreateHandler(webapp2.RequestHandler):
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		
		deal_text = self.request.get('deal_text')
		img_key = self.request.get('img_key')
		
		if deal_text == "":
			error = 'Please describe your offer'
		else:
			error = None 
		
		if error:
			template_values = {
				"title"		:	"Describe your offer",
				"deal_text"	:	deal_text,
				"img_key"	:	img_key,
				"error"		:	error
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-dealtext.html')
			self.response.out.write(template.render(template_values))
		
		else:
			template_values = {
				"title"		:	"Anything else?",
				"deal_text"	:	deal_text,
				"img_key"	:	img_key
			}
			
			template = jinja_environment.get_template('templates/merchants-mobile-description.html')
			self.response.out.write(template.render(template_values))
		
class MobileDealTextEditHandler(webapp2.RequestHandler):
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		self.response.out.write(meta)
		
class MobileDescriptionCreateHandler(webapp2.RequestHandler):
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		
		deal_text = self.request.get('deal_text')
		description = self.request.get('description')
		img_key = self.request.get('img_key')
		
		logging.info(deal_text)
		logging.info(img_key)
		logging.info(description)
		
class MobileDescriptionEditHandler(webapp2.RequestHandler):
	def post(self):
		meta = merchant_utils.login_check_mobile(self)
		self.response.out.write(meta)
		


class MerchantsHandler(webapp2.RequestHandler):
	def get(self):
		#check if logged in. if so, redirect to the manage page
		session = get_current_session()
		if session.has_key('loggedIn') == True and session['loggedIn'] == True:
			self.redirect("/merchants/manage")
		else:
			template = jinja_environment.get_template('templates/merchants.html')
			self.response.out.write(template.render())
			
class MerchantsBetaHandler(webapp2.RequestHandler):
	def get(self):
		#check if logged in. if so, redirect to the manage page
		session = get_current_session()
		if session.has_key('loggedIn') == True and session['loggedIn'] == True:
			self.redirect("/merchants/manage")
		else:
			template = jinja_environment.get_template('templates/merchants_beta.html')
			self.response.out.write(template.render())

class MerchantsBetaRequestHandler(webapp2.RequestHandler):
	def post(self):
		
		#grab the inputs
		business_name = self.request.get('business_name')
		business_type = self.request.get('business_type')
		city = self.request.get('city')
		owner_name = self.request.get('owner_name')
		owner_email = self.request.get('owner_email')
		use_case = self.request.get('use_case')
		
		#error check
		if business_name == '':
			error = 'Please enter the name of your business.'
		elif business_type == '':
			error = 'Please enter what your business sells.'
		elif city == '':
			error = 'Please enter your city.'
		elif owner_name == '':
			error = 'Please enter your name.'
		elif owner_email == '':
			error = 'Please enter your email.'
		else:
			error = None
		
		if error:
			template_values = {
				'error'	: error,
				'business_name' : business_name,
				'business_type'	: business_type,
				'city'			: city,
				'owner_name'	: owner_name,
				'owner_email'	: owner_email,
				'use_case'		: use_case
			}
			logging.info(template_values)
			template = jinja_environment.get_template('templates/merchants_beta.html')
			self.response.out.write(template.render(template_values))
		else:
			#create the business beta request object
			beta = levr.BusinessBetaRequest(
				business_name=business_name,
				business_type=business_type,
				city=city,
				owner_name=owner_name,
				owner_email=owner_email,
				use_case=use_case
			).put()
			
			logging.info(levr.log_model_props(beta))
			
			#write out the success page
			template = jinja_environment.get_template('templates/merchants_beta_success.html')
			self.response.out.write(template.render())
			
			#send to mixpanel
			
			properties = {
				'$business_name' : business_name,
				'$business_type'	: business_type,
				'$city'			: city,
				'$owner_name'	: owner_name,
				'$email'		: owner_email,
				'$use_case'		: use_case
			}
			
			#mp_track.track('Business beta request',"70b2a36876730d894bce115f3e89c055",properties)
			
			#mp_track.person(owner_email,'70b2a36876730d894bce115f3e89c055',properties)


class LoginHandler(webapp2.RequestHandler):
	def get(self):
		
		email = self.request.get('email').lower()
		password = self.request.get('password')
		
		
		template_values = {
			'email'		:	email,
			'password'	:	password
		}
		
		if merchant_utils.check_ua(self) == 'mobile':
			template = jinja_environment.get_template('templates/login_mobile.html')
		else:
			template = jinja_environment.get_template('templates/login.html')
			
		self.response.out.write(template.render(template_values))
		
	def post(self):
		try:
		
			email = self.request.get('email').lower()
			password = self.request.get('password')
			
			if password != '':
				password = enc.encrypt_password(password)
				
				logging.info(email)
				logging.info(password)
				
				#check for this user
				user = levr.Customer.gql('WHERE email=:1 AND pw=:2',email,password).get()
				
				if not user:
					#simulate an error
					error = "Your username or password isn't quite right. Please try again."
					template_values = {
						'email'		:	email,
						'password'	:	enc.decrypt_password(password),
						'error'		:	error,
						'layout'	:	merchant_utils.check_ua(self)
					}
					
					template = jinja_environment.get_template('templates/login.html')
					self.response.out.write(template.render(template_values))
				else:
					
					#is this some fool ninja trying to log in online?
					if not user.owner_of:
						self.redirect('http://www.levr.com')
					else:
						#logged in, start a session and all that jazz
						session = get_current_session()
						session['uid'] = enc.encrypt_key(user.key())
						session['loggedIn'] = True
						session['validated'] = merchant_utils.validated_check(user)
						session['owner_of']	=	enc.encrypt_key(user.owner_of)
						
						#send to the merchants page
						self.redirect('/merchants/mobile/manage')
				
				
			else:
				error = "Please enter a password."
				template_values = {
					'email'		:	email,
					'error'		:	error
				}
				template = jinja_environment.get_template('templates/login.html')
				self.response.out.write(template.render(template_values))
			
			
			
			'''
			#this is passed when an ajax form is checking the login state
			email = self.request.get('email')
			pw = enc.encrypt_password(self.request.get('pw'))
			
			if self.request.get('type') == 'ajax':
				logging.debug('AJAX CHECK')
	
				#check if login is valid
				q = levr.BusinessOwner.gql('WHERE email =:1 AND pw =:2', email, pw)
				if q.get():
					#echo that login was successful
					self.response.out.write(True)
				else:
					#echo that login was not successful
					self.response.out.write(False)
			else:
				#Normal login attempt. Redirects to manage or the login page
				email = self.request.get('email')
#				email = db.Email(email)
				pw = enc.encrypt_password(self.request.get('pw'))
				logging.debug(email)
				logging.debug(pw)
				
				if email == None:
					email = ''
				if pw == None:
					pw = ''
				
				
				#the required text fields were entered
				#query database for matching email and pw
				owner = levr.BusinessOwner.all().filter('email =', email).filter('pw =', pw).get()
				#search for owner
				logging.debug(owner)
				if owner != None:
					logging.debug('owner exists... login')
					#owner exists in db, and can login
					session = get_current_session()
					session['ownerID'] = enc.encrypt_key(owner.key())#business.key())
					session['loggedIn'] = True
					session['validated'] = owner.validated
					self.redirect('/merchants/manage')
				else:
					#show login page again - login failed
					template_values = {
					'success'		: False,
					'email'			: email
					}
					template = jinja_environment.get_template('templates/login.html')
					self.response.out.write(template.render(template_values))
#					self.response.out.write(template_values)
'''
		except:
			levr.log_error()

class LogoutHandler(webapp2.RequestHandler):
	def get(self):
		try:
			session = get_current_session()
			session['loggedIn'] = False
			self.redirect('/merchants/login')
		
		except:
			levr.log_error()

class LostPasswordHandler(webapp2.RequestHandler):
	'''presents form to user to enter in their email. email is sent to user
	to rest the password'''
	
	def post(self):
		'''input:user email
		output: success, sends email to email account'''
		try: 
			user_email = self.request.get('email')
			user = levr.BusinessOwner.all().filter('email =', user_email).get()
			logging.debug(user)
			if not user:
				logging.debug('flag not user')
				self.redirect('/merchants/login?action=password&success=False')
			else:
				logging.debug('flag is user')
				#send mail to the admins to notify of new pending deal
				url = levr_utils.URL+'/merchants/password/reset?id=' + enc.encrypt_key(user.key())
				logging.info(url)
				try:
					message = mail.EmailMessage(
						sender	="Levr <patrick@levr.com>",
						subject	="Reset Password",
						to		=user.email)
					logging.debug(message)
					body = 'Hello,\n\n'
					body += "To reset your Levr password, please follow this link.\n\n"
					body += url+"\n\n"
					body += "If you did not request this password reset, please ignore this email.\n\n"
					body += "Regards,\n\n"
					body += "The Levr Team"
					message.body = body
					message.send()
					logging.debug(body)
					logging.debug(url)
#					sent = True
				except:
#					sent = False
					logging.error('mail not sent')
					self.redirect('/merchants/login?action=password&success=false')
					
				else:
#					template_values={"sent":sent}
					self.redirect('/merchants/login?action=password&success=true')
		except:
			levr.log_error()
		
class ResetPasswordHandler(webapp2.RequestHandler):
	'''User enters in a new password twice'''
	def get(self):
		try:
			'''Template has uid in url to identify them'''
			
			uid = self.request.get('id')
			#If a false attempt has been made, success will be false, otherwise true
			try:
				success = self.request.get('success')
			except:
				success = 'True'
			
			
			template_values = {
							"success"	:success,
							"uid"		:uid,
							"action"	:'reset'
							}
				
			template = jinja_environment.get_template('templates/login.html')
			self.response.out.write(template.render(template_values))
		except:
			levr.log_error()
	def post(self):
		'''Resets password on the database'''
		try:
			password1 = self.request.get('newPassword1')
			password2 = self.request.get('newPassword2')
			uid = self.request.get('id')
			uid = enc.decrypt_key(uid)
			
			if password1 == password2:
				#passwords match
				logging.debug('flag password success')
				encrypted_password = enc.encrypt_password(password1)
				logging.debug(uid)
				owner = levr.BusinessOwner.get(uid)
				owner.pw = encrypted_password
				owner.put()
				
				#log user in and redirect them to merchants/manage
				session = get_current_session()
				session['ownerID'] = enc.encrypt_key(owner.key())#business.key())
				session['loggedIn'] = True
				session['validated'] = owner.validated
				self.redirect('/merchants/manage')
				
			else:
				#passwords do not match
				self.redirect('/merchants/password/reset?id=%s&success=False' % enc.encrypt_key(uid))
		except:
			levr.log_error()
class EmailCheckHandler(webapp2.RequestHandler):
	def post(self):
		'''This is currently a handler to check whether the email entered by a business on signup is available'''
		email = self.request.get('email').lower()
		#pw = enc.encrypt_password(self.request.get('pw'))
		
		#check if email is already in use
		existing_merchant = levr.Customer.gql('WHERE email=:1', email).get()
		if existing_merchant:
			#echo that email is in use
			self.response.out.write(False)
		else:
			#echo that email is available
			self.response.out.write(True)


class WelcomeHandler(webapp2.RequestHandler):
	def get(self):
		try:
			if merchant_utils.check_ua(self) == 'mobile':
				template = jinja_environment.get_template('templates/new_mobile.html')
			else:
				template = jinja_environment.get_template('templates/new.html')
				
			self.response.out.write(template.render())
		except:
			levr.log_error()
	def post(self):
			#A business owner is signing up in the tour
		try:
			logging.debug(self.request.headers)
			logging.debug(self.request.body)
			logging.debug(self.request.params)
			
			#get the business info from the form
			business_name	= self.request.get('business_name')
			phone			= self.request.get('phone')
			geo_point		= levr.geo_converter(self.request.get('geo_point'))
			vicinity		= self.request.get('vicinity')
			types			= self.request.get_all('types[]')
			
			#check if that business already exists
			business = levr.Business.all().filter('business_name =', business_name).filter('vicinity =',vicinity).get()
			
			if not business:
				logging.info('business does not exist...creating')
				#create the business
				business = levr.Business(
						business_name=business_name,
						geo_point = geo_point,
						geo_hash = geohash.encode(geo_point.lat,geo_point.lon),
						vicinity = vicinity,
						types = types,
						phone = phone
				)
				
				business.put()
			
			else:
				#even if there is a business, grab it and update it if the phone number is null
				if not business.phone:
					business.phone = self.request.get('phone')
					business.put()
				
			#at this point, a business should exist
			logging.debug(levr.log_model_props(business))
			
			#create the owner
			owner = levr.Customer(
				email=self.request.get('email').lower(),
				pw=enc.encrypt_password(self.request.get('password')),
				owner_of=str(business.key()),
				levr_token=levr.create_levr_token(),
				display_name=business.business_name,
				alias=business.business_name
			)
			
			owner.put()
			
			logging.debug(levr.log_model_props(owner))
			
			#log the owner in
			session = get_current_session()
			session['uid']	= enc.encrypt_key(str(owner.key()))
			session['loggedIn']	= True
			session['validated']= False
			session['owner_of']	=	enc.encrypt_key(owner.owner_of)
			logging.debug(session)
			
			
			self.redirect('/merchants/manage')
			
			
			
			
			'''
			owner = levr.Customer(
				#create owner with contact info, put and get key
				email			=self.request.get('email'),
				pw				=enc.encrypt_password(self.request.get('password')),
				validated		=False
				).put()
			logging.debug(owner)
			
			#get the business info from the form
			business_name	= self.request.get('business_name')
			geo_point		= levr.geo_converter(self.request.get('geo_point'))
			vicinity		= self.request.get('vicinity')
			types			= self.request.get_all('types[]')
			
			#parse business name to create an upload email
			logging.debug(business_name)
			name_str = levr.tagger(business_name)
			logging.debug(name_str)
			#create unique identifier for the business
			# if name_str[0] == 'the' or name_str[0] == 'a' or name_str[0] == 'an':
# 				#dont like the word the in front
# 				logging.debug('flag the!')
# 				identifier = ''.join(name_str[1:3])
# 			else:
# 				identifier = ''.join(name_str[:2])
# 			upload_email = "u+"+identifier+"@levr.com"
			
			#check if that already exists
			num = levr.Business.all().filter('upload_email =',upload_email).count()
			
			logging.debug(num)
			if num != 0:
				#a business already exists with that upload email
				#increment the 
				upload_email = "u+"+identifier+str(num)+"@levr.com"
			
			logging.debug(upload_email)
			
			#check if business exists in database
			business = levr.Business.all().filter('business_name =', business_name).filter('vicinity =',vicinity).get()
			logging.debug(business)
			
			if business:
				logging.debug(levr_utils.log_model_props(business))
				logging.debug(owner)
				logging.debug(upload_email)
				logging.debug('flag business already exists')
				#have to delete business entity instead of update because gae wont update reference on owner entity
				if business.owner == None:
					#grab this business! 
					business.owner	= owner
# 					upload_email	= upload_email
					#TODO targeted will be set to false in the future, removing signed businesses from the ninja pool
#					targeted		= False
				else:
#					db.delete(business)
					logging.error('A business owner just signed up claiming a business that another person has claimed')
			else:
				logging.debug('flag business does not exist')
			
				#create business entity
				business = levr.Business(
					#create business
					owner			=owner,
					business_name	=business_name,
					vicinity		=vicinity,
					geo_point		=geo_point,
					types			=types,
					upload_email	=upload_email
					#TODO targeted will be set to false in the future, removing signed businesses from the ninja pool
#					targeted		=False
					)
			logging.debug(levr_utils.log_model_props(business))
			business.put()
			
			#creates new session for the new business
			session = get_current_session()
			session['ownerID']	= enc.encrypt_key(owner)
			session['loggedIn']	= True
			session['validated']= False
			logging.debug(session)


			#send email to pat so that he will know that there is a new business.
			message = mail.EmailMessage(
				sender	="LEVR AUTOMATED <patrick@levr.com>",
				subject	="New Merchant signup",
				to		="patrick@levr.com")
			logging.debug(message)
			body = 'New merchant\n\n'
			body += 'Business: '  +str(business_name)+"\n\n"
			body += 'Business ID: '+str(business)+"\n\n"
			body += "Owner Email:"+str(self.request.get('email'))+"\n\n"
			message.body = body
			message.send()
			

			#forward to appropriate page
			if self.request.get('destination') == 'upload':
				self.redirect('/merchants/upload')
			elif self.request.get('destination') == 'create':
				self.redirect('/merchants/deal')
			'''
		except:
			levr.log_error(self.request.body)

class DealHandler(webapp2.RequestHandler):
	def get(self):
		'''This is the deal upload page'''
		try:
			#check login
			headerData = merchant_utils.login_check(self)
			logging.debug(headerData)
			#get the owner information
			uid = headerData['uid']
			user = levr.Customer.get(uid)
			logging.info(levr.log_model_props(user))
			#get the business
			business = levr.Business.get(headerData['owner_of'])	
			logging.info(levr.log_model_props(business))
			
			blobstore.create_upload_url('/merchants/upload')
			
			template_values = {
							"upload_url"	: blobstore.create_upload_url('/merchants/deal/upload'),
							"deal"			: None,
							"business"		: business, #TODO need to grab multiple businesses later
							"user"			: user
			}
			
			if merchant_utils.check_ua(self) == 'mobile':
				template = jinja_environment.get_template('templates/deal_mobile.html')
			else:
				template_values.update({'validated'		: merchant_utils.validated_check(user)})
				template = jinja_environment.get_template('templates/deal.html')
			self.response.out.write(template.render(template_values))
		except:
			levr.log_error()
		'''upload_url = blobstore.create_upload_url('/merchants/deal/upload')
		self.response.out.write('<html><body>')
		self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
		self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit"
			 name="submit" value="Submit"> </form></body></html>""")'''
			
			
class DealUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
#class DealUploadHandler(webapp2.RequestHandler):
	def post(self):
		try:
			#A merchant is creating a NEW deal from the online form
# 			logging.info('hi there')
			#check login
			headerData = merchant_utils.login_check(self)
			logging.debug(headerData)
			#get the owner information
			uid = headerData['uid']
			user = levr.Customer.get(uid)
			
			if self.get_uploads(): #will this work?
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
				upload_flag = True
			else:
				upload_flag = False
				raise KeyError('Image was not uploaded')
			
			# TODO: too many deal creations
			#initialize the deal - just the stuff from the input here
			deal = levr.Deal(
				img				=	img_key,
				deal_text		=	self.request.get('deal_text'),
				description		=	self.request.get('description'),
				parent			=	user.key()
			)
			
			#add all the properties from the business
			business = levr.Business.get(user.owner_of)
			logging.info(levr.log_model_props(business))
			
			#kick over to create_deal to finish the deal creation
			deal = merchant_utils.create_deal(deal,business,user)
			
			#log via mixpanel
			
			self.redirect('/merchants/manage')
			
			#if not validated set deal status to "pending", otherwise set it to "active"
		# 	if merchant_utils.validated_check(user):
# 				logging.deug('OKAY')
# 			else:
# 				logging.debug('FUCK ALL')
			
			#pass it to the create_deal function to 
			
			
			
			
			'''
			#make sure than an image is uploaded
			# logging.debug(self.get_uploads())
			if self.get_uploads(): #will this work?
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
			else:
				raise Exception('Image was not uploaded')
			
			params = {
					'uid'				:self.request.get('uid'),
					'business'			:self.request.get('business'),
					'deal_description'	:self.request.get('deal_description'),
					'deal_line1'		:self.request.get('deal_line1'),
					'deal_line2'		:self.request.get('deal_line2'),
					'img_key'			:img_key
					}
			levr_utils.dealCreate(params, 'merchant_create')
			self.redirect('/merchants/manage')'''
		except:
			levr.log_error(self.request.body)
			
class DealUpdateHandler(blobstore_handlers.BlobstoreUploadHandler):
#class DealUploadHandler(webapp2.RequestHandler):
	def post(self):
		try:
			#A merchant is updating an existing deal from the update form
# 			logging.info('hi there')
			#check login
			headerData = merchant_utils.login_check(self)
			logging.debug(headerData)
			#get the owner information
			uid = headerData['uid']
			user = levr.Customer.get(uid)
			
			if self.get_uploads(): #will this work?
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
				upload_flag = True
			else:
				upload_flag = False
				
			#grab the deal
			dealID = self.request.get('dealID')
			dealID = enc.decrypt_key(dealID)
			deal = levr.Deal.get(dealID)
			
			#grab the business
			business = levr.Business.get(deal.businessID)
			
			#is there an image to update?
			if upload_flag == True:
				#grab the old blob key
				old_blob = deal.img
# 				#grab the old blob
# 				old_blob = blobstore.BlobInfo.get(old_key)
				#set the new key
				deal.img = img_key
				#delete the old blob
				old_blob.delete()
			
			#update all the other fields
			deal.deal_text = self.request.get('deal_text')
			deal.description = self.request.get('description')
			
			#update the tags
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
			deal.tags = tags
			
			deal.put()
			
			#fire off a request to rotate the image if necessary
			#fire off a task to do the image rotation stuff
			task_params = {
				'blob_key'	:	str(deal.img.key())
			}
			taskqueue.add(url='/tasks/checkImageRotationTask',payload=json.dumps(task_params))
			
			self.redirect('/merchants/manage')
			
			
			#initialize the deal - just the stuff from the input here
# 			deal = levr.Deal(
# 				img				=	img_key,
# 				deal_text		=	self.request.get('deal_text'),
# 				description		=	self.request.get('description'),
# 				parent			=	user.key()
# 			)
# 			
# 			#add all the properties from the business
# 			business = levr.Business.get(user.owner_of)
# 			logging.info(levr.log_model_props(business))
# 			
# 			#kick over to create_deal to finish the deal creation
# 			deal = merchant_utils.create_deal(deal,business,user)
# 			
# 			self.redirect('/merchants/manage')
			
			#if not validated set deal status to "pending", otherwise set it to "active"
		# 	if merchant_utils.validated_check(user):
# 				logging.deug('OKAY')
# 			else:
# 				logging.debug('FUCK ALL')
			
			#pass it to the create_deal function to 
			
			
			
			
			'''
			#make sure than an image is uploaded
			# logging.debug(self.get_uploads())
			if self.get_uploads(): #will this work?
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
			else:
				raise Exception('Image was not uploaded')
			
			params = {
					'uid'				:self.request.get('uid'),
					'business'			:self.request.get('business'),
					'deal_description'	:self.request.get('deal_description'),
					'deal_line1'		:self.request.get('deal_line1'),
					'deal_line2'		:self.request.get('deal_line2'),
					'img_key'			:img_key
					}
			levr_utils.dealCreate(params, 'merchant_create')
			self.redirect('/merchants/manage')'''
		except:
			levr.log_error(self.request.body)
			
class DeleteDealHandler(webapp2.RequestHandler):
	def get(self,dealID):
		try:
			headerData = merchant_utils.login_check(self)
			dealID = enc.decrypt_key(dealID)
			owner = levr.Customer.get(headerData['uid'])
			deal = levr.Deal.get(dealID)
			#make sure this merchant is the owner of the deal before deleting
			if deal.key().parent() == owner.key():
				logging.info('keys match!')
				#delete the deal
				deal.deal_status = 'expired'
				deal.put()
				#redirect to manage
				self.redirect('/merchants/manage')
			else:
				logging.info('key mismatch')
				#bounce to login page
				self.redirect('/merchants/login')
# 			deal = levr.Deal.get(dealID)
# 			logging.info(levr.log_model_props(deal))
			# logging.debug(self.request)
# 			dealID = self.request.get('id')
# 			dealID = enc.decrypt_key(dealID)
# 			db.delete(dealID)
# 			
# 			self.redirect('/merchants/manage')
		except:
			levr.log_error()
			
class ReanimateDealHandler(webapp2.RequestHandler):
	def get(self,dealID):
		try:
			headerData = merchant_utils.login_check(self)
			dealID = enc.decrypt_key(dealID)
			owner = levr.Customer.get(headerData['uid'])
			deal = levr.Deal.get(dealID)
			#make sure this merchant is the owner of the deal before deleting
			if deal.key().parent() == owner.key():
				logging.info('keys match!')
				#delete the deal
				deal.deal_status = 'active'
				deal.put()
				#redirect to manage
				self.redirect('/merchants/manage')
			else:
				logging.info('key mismatch')
				#bounce to login page
				self.redirect('/merchants/login')
# 			deal = levr.Deal.get(dealID)
# 			logging.info(levr.log_model_props(deal))
			# logging.debug(self.request)
# 			dealID = self.request.get('id')
# 			dealID = enc.decrypt_key(dealID)
# 			db.delete(dealID)
# 			
# 			self.redirect('/merchants/manage')
		except:
			levr.log_error()
			

class EditDealHandler(webapp2.RequestHandler):
	def get(self):
		try:
			#check login
			headerData = merchant_utils.login_check(self)
			dealID = enc.decrypt_key(self.request.get('dealID'))
			owner = levr.Customer.get(headerData['uid'])
			business = levr.Business.get(owner.owner_of)
			
			deal = levr.Deal.get(dealID)
			
			deal.enc_key = enc.encrypt_key(deal.key())
			deal.img_url = api_utils.create_img_url(deal,'large')
			
			template_values = {
				'deal'		:	deal,
				'business'	:	business,
				'user'		:	owner,
				"upload_url"	: blobstore.create_upload_url('/merchants/deal/update')
			}
			
			if merchant_utils.check_ua(self) == 'mobile':
				template = jinja_environment.get_template('templates/deal_mobile.html')
			else:
				template_values.update({'validated'		: merchant_utils.validated_check(owner)})
				template = jinja_environment.get_template('templates/deal.html')
			self.response.out.write(template.render(template_values))
			
			
			'''
			#get the owner information
			ownerID = headerData['ownerID']
			ownerID = enc.decrypt_key(ownerID)
			ownerID = db.Key(ownerID)
			owner = levr.BusinessOwner.get(ownerID)
			logging.debug(owner)
			
			#get the business
			business = owner.businesses.get()
			
			#get deal
			dealID = self.request.get('id')
			
			
			#create upload url BEFORE DECRYPTING
			url = '/merchants/editDeal/upload?uid=' + headerData['ownerID'] + '&business='+ enc.encrypt_key(business.key()) +'&deal=' + dealID
			upload_url = blobstore.create_upload_url(url)
			
			
			#decrypt id, get and format deal
			dealID = enc.decrypt_key(dealID)
			deal = levr.Deal.get(dealID)
			deal = levr.phoneFormat(deal, 'manage')
			
			template_values = {
							"edit"		:True,
							"upload_url":upload_url,
							"deal"		:deal,
							"owner"		:owner,
							"business"	:business,
							"headerData":headerData
			}
			template = jinja_environment.get_template('templates/deal.html')
			self.response.out.write(template.render(template_values))'''
		except:
			levr.log_error()
class EditDealUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		try:
			#A merchant is EDITING a deal from the online form
			logging.debug(self.request.params)
			
			#make sure than an image is uploaded
			logging.debug(self.get_uploads())
			if self.get_uploads().__len__()>0: #will this work?
				#image has been uploaded
				upload_flag = True
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
			else:
				#image has not been uploaded
				upload_flag = False
				img_key = ''
			logging.debug('upload_flag: '+str(upload_flag))
			params = {
					'uid'				:self.request.get('uid'),
					'business'			:self.request.get('business'),
					'deal'				:self.request.get('deal'),
					'deal_description'	:self.request.get('deal_description'),
					'deal_line1'		:self.request.get('deal_line1'),
					'deal_line2'		:self.request.get('deal_line2'),
					'img_key'			:img_key
					}
			
			levr_utils.dealCreate(params, 'merchant_edit',upload_flag)
			self.redirect('/merchants/manage')
		except:
			levr.log_error(self.request.body)
			
class VerifyHandler(webapp2.RequestHandler):
	def get(self):
		
		#check login
		headerData = merchant_utils.login_check(self)
		
		#get the owner information
		uid = headerData['uid']
		owner = levr.Customer.get(uid)
		logging.info(levr.log_model_props(owner))
		
		#get the business
		business = levr.Business.get(headerData['owner_of'])
		logging.info(levr.log_model_props(business))
		
		#check if the owner already has an activation code
		if owner.activation_code:
			activation_code = owner.activation_code
		else:
			activation_code = str(int(time.time()))[-4:]
			owner.activation_code = activation_code
			owner.put()
		
		#write out this page
		template_values = {
			'business'			:	business,
			'activation_code'	:	activation_code
		}
		
		logging.info(template_values)
		
		if merchant_utils.check_ua(self) == 'mobile':
			template = jinja_environment.get_template('templates/merchant_verify_mobile.html')
		else:
			template = jinja_environment.get_template('templates/merchant_verify.html')
		self.response.out.write(template.render(template_values))


class VerifyCallHandler(webapp2.RequestHandler):
	def get(self):
		#check login
		headerData = merchant_utils.login_check(self)
		
		#get the owner information
		uid = headerData['uid']
		owner = levr.Customer.get(uid)
		logging.info(levr.log_model_props(owner))
		
		#get the business
		business = levr.Business.get(headerData['owner_of'])
		logging.info(levr.log_model_props(business))
		
		#check if the owner already has an activation code
		if owner.activation_code:
			activation_code = owner.activation_code
		else:
			activation_code = str(int(time.time()))[-4:]
			owner.activation_code = activation_code
			owner.put()
			
		#call the business
		merchant_utils.call_merchant(business)
		
		#write out this page
		template_values = {
			'business'			:	business,
			'activation_code'	:	activation_code,
			'call_in_progress'	:	True
		}
		
		logging.info(template_values)
		
		if merchant_utils.check_ua(self) == 'mobile':
			template = jinja_environment.get_template('templates/merchant_verify_mobile.html')
		else:
			template = jinja_environment.get_template('templates/merchant_verify.html')
		self.response.out.write(template.render(template_values))

class VerifyAnswerHandler(webapp2.RequestHandler):
	def post(self):
	
		request = json.loads(self.request.body)
		logging.debug(request)
		
		self.response.out.write('''<?xml version="1.0" encoding="UTF-8"?>
		<Response>
			<Gather timeout="10" finishOnKey="*" action="http://www.levr.com/api/merchant/twiliocheckcode">
				<Say>Thanks for using Levr!</Say>
				<Say>Please enter your activation code and then press star.</Say>
			</Gather>
		</Response>''')


class VerifyStatusCallbackHandler(webapp2.RequestHandler):
	def post(self):
		logging.debug(self.request.body)
		#code = self.request.get('Digits')
		#callto = self.request.get('To')


class ManageHandler(webapp2.RequestHandler):
	def get(self):
		try:
			#check login
			headerData = merchant_utils.login_check(self)
			
			#get the owner information
			uid = headerData['uid']
			user = levr.Customer.get(uid)
			logging.info(levr.log_model_props(user))
			#get the business
			business = levr.Business.get(headerData['owner_of'])
			logging.info(levr.log_model_props(business))
			
			#grab the deals
			q_deals = levr.Deal.gql('WHERE ANCESTOR IS :1 ORDER BY deal_views DESC',user.key())
			logging.info(q_deals.count())
			#package
			deals = []
			active = []
			pending = []
			expired = []
			for deal in q_deals:
				deal.enc_key = enc.encrypt_key(deal.key())
				logging.info(deal.deal_status)
				if deal.deal_status == 'active':
					active.append(deal)
					logging.info('appended to active')
				elif deal.deal_status == 'pending':
					pending.append(deal)
					logging.info('appended to pending')
				elif deal.deal_status == 'expired':
					expired.append(deal)
					logging.info('appended to expired')
			'''
			#sort each list based on views
			sorted_active = sorted(active, key=lambda k: k.deal_views)
			sorted_pending = sorted(pending, key=lambda k: k.deal_views)
			for deal in expired:
				logging.info(deal.deal_views)
			sorted_expired = sorted(expired, key=lambda k: k.deal_views)
			logging.info('sorted:')
			for deal in sorted_expired:
				logging.info(deal.deal_views)
			
			
			deals = sorted_active + sorted_pending + sorted_expired
			'''
			deals = active + pending + expired
			logging.info(deals)
			
			
			template_values = {
				'headerData':headerData,
				'title'		:'Manage',
				'user'		:user,
				'business'	:business,
				'deals'		:deals,
				'validated'	: merchant_utils.validated_check(user)
			}
			
			
			logging.info(template_values)
			
			if merchant_utils.check_ua(self) == 'mobile':
				template = jinja_environment.get_template('templates/manageOffers_mobile.html')
			else:
				template = jinja_environment.get_template('templates/manageOffers.html')
				
			self.response.out.write(template.render(template_values))
			
			'''
			#get all deals that are children of the owner ordered by whether or not they are exclusive or not
#			d = levr.Deal.all().ancestor(ownerID).order("is_exclusive").fetch(None)
#			logging.debug(d)
			#get all ninja deals
			d = levr.Deal().all().filter('businessID =', str(business.key())).fetch(None)
#			d += ninja_deals
			#package deals - mostly for getting the correct urls
			deals = []
			for deal in d:
				logging.debug('-----------')
				deals.append(levr.phoneFormat(deal, 'manage'))
			
			
			
			
			template_values = {
				'headerData':headerData,
				'title'		:'Manage',
				'owner'		:owner,
				'business'	:business,
				'deals'		:deals,
				'views'		:views,
				'rank'		:rank,
				'redemptions':redemptions
			}
			logging.debug(template_values)
			
			template = jinja_environment.get_template('templates/manageOffers.html')
			self.response.out.write(template.render(template_values))'''
		except:
			levr.log_error()

class UploadHandler(webapp2.RequestHandler):
	def get(self):
		'''This is for the page where they see info about how to upload via email'''
		try:
			#check login
			headerData = levr_utils.loginCheck(self, True)
			
			#get the owner information
			ownerID = headerData['ownerID']
			ownerID = enc.decrypt_key(ownerID)
			ownerID = db.Key(ownerID)
			owner = levr.BusinessOwner.get(ownerID)
			logging.debug(owner)
			if not owner:
				self.redirect('/merchants')
			
			#get the business
			business = owner.businesses.get()
			
			
			template_values = {
				'headerData':headerData,
				'title'		:'Upload Instructions',
				'owner'		:owner,
				'business'	:business
			}
			
			template = jinja_environment.get_template('templates/emailUpload.html')
			self.response.out.write(template.render(template_values))
		except:
			levr.log_error()
class WidgetHandler(webapp2.RequestHandler):
	def get(self):
		'''The page where they view info about the widget'''
		try:
			headerData = levr_utils.loginCheck(self, True)
			logging.debug(headerData)
			
			ownerID = headerData['ownerID']
			ownerID = enc.decrypt_key(ownerID)
			
			
			#business info
			business	= levr.Business.all().filter('owner = ',db.Key(ownerID)).get()
			logging.debug(business)
			
			#businessID
			businessID	= enc.encrypt_key(business.key())
			
			#iframe
			frame = "&lt;iframe src='"+levr_utils.URL+"/widget?id="+business.widget_id+"' frameborder='0' width='1000' height='400' &gt;Your Widget&lt;/iframe&gt; />"
		
#			frame = "<iframe src='/widget?id="+business.widget_id+"' frameborder='0' width='1000' height='400' >Your Widget</iframe>"
			logging.debug(frame)
			
			
			template_values = {
				'business'		: business,
				'businessID'	: businessID,
				'frame'			: frame
			}
			template = jinja_environment.get_template('templates/manageWidget.html')
			self.response.out.write(template.render(template_values))
		except:
			levr.log_error()
class MyAccountHandler(webapp2.RequestHandler):
	def get(self):
		try:
			#check login
			headerData = levr_utils.loginCheck(self, True)
			
			#get the owner information
			ownerID = headerData['ownerID']
			ownerID = enc.decrypt_key(ownerID)
			ownerID = db.Key(ownerID)
			owner = levr.BusinessOwner.get(ownerID)
			logging.debug(owner)
			
			#get the business
			business = owner.businesses.get()
			
			template_values = {
				'owner'		: owner,
				'business'	: business,
				'mode'		: '', #which form to show
				'error'		: ''
				}
				
			template = jinja_environment.get_template('templates/editAccount.html')
			self.response.out.write(template.render(template_values))
		except:
			levr.log_error()
	def post(self):
		try:
			logging.debug(self.request.headers)
			logging.debug(self.request.body)
			logging.debug(self.request.params)
			
			#check login
			headerData = levr_utils.loginCheck(self, True)
			
			#get the owner information
			ownerID = headerData['ownerID']
			ownerID = enc.decrypt_key(ownerID)
			ownerID = db.Key(ownerID)
			owner = levr.BusinessOwner.get(ownerID)
			logging.debug(owner)
			
			password = enc.encrypt_password(self.request.get('old_password'))
			mode = self.request.get('change')
			logging.debug(owner.pw == password)
			if owner.pw == password:
				
				#password is correct
				
				if mode == 'email':
					#user is changing their email
					
					email			= self.request.get('new_email')
					confirm_email	= self.request.get('confirm_new_email')
					if email == confirm_email:
						logging.debug(email)
						#emails match - change owner email
						owner.email = email
						owner.put()
						self.redirect('/merchants/myAccount?success=true')
					else:
						#get the business
						business = owner.businesses.get()
						
						template_values = {
						'owner'		: owner,
						'business'	: business,
						'mode'		: mode, #which form to show
						'error'		: 'confirm_new_email'
						}
						logging.debug(template_values)
						#password is incorrect
						template = jinja_environment.get_template('templates/editAccount.html')
						self.response.out.write(template.render(template_values))
					
				elif mode == 'password':
					#user is changing their password
					new_password		= self.request.get('new_password')
					confirm_new_password= self.request.get('confirm_new_password')
					
					if new_password == confirm_new_password:
						logging.debug(new_password)
						#passwords match - change owner password
						owner.pw = new_password
						owner.put()
						self.redirect('/merchants/myAccount?success=true')
					else:
						#new passwords do not match
						#get the business
						business = owner.businesses.get()
						
						template_values = {
						'owner'		: owner,
						'business'	: business,
						'mode'		: mode, #which form to show
						'error'		: 'confirm_new_password'
						}
				
						#password is incorrect
						template = jinja_environment.get_template('templates/editAccount.html')
						self.response.out.write(template.render(template_values))
				else:
					#mode not recognized
					logging.error('mode not recognized')
			else:
				#old password is incorrect
				#get the business
				business = owner.businesses.get()
				
				template_values = {
				'owner'		: owner,
				'business'	: business,
				'mode'		: mode, #which form to show
				'error'		: 'old_password'
				}
				
				logging.debug(template_values)
				template = jinja_environment.get_template('templates/editAccount.html')
				self.response.out.write(template.render(template_values))
		except:
			levr.log_error(self.request.headers)
			
class CheckPasswordHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.debug(self.request.headers)
			logging.debug(self.request.body)
			logging.debug(self.request.params)
			#ajshdbashjbdhjasbdjhasbdjhasb
			
			
			#check login
			headerData = levr_utils.loginCheck(self, True)
			
			#get the owner information
			ownerID = headerData['ownerID']
			ownerID = enc.decrypt_key(ownerID)
			ownerID = db.Key(ownerID)
			owner = levr.BusinessOwner.get(ownerID)
			logging.debug(owner)
			
			password = enc.encrypt_password(self.request.get('password'))
			if owner.pw == password:
				self.response.out.write(True)
			else:
				self.response.out.write(False)
			
		except:
			levr.log_error()
		

app = webapp2.WSGIApplication([('/merchants/mobile',MobileLandingHandler),
								('/merchants/mobile/login',MobileLoginHandler),
								('/merchants/mobile/logout',MobileLogoutHandler),
								('/merchants/mobile/businessselect',MobileBusinessSelectHandler),
								('/merchants/mobile/autocomplete',MobileAutocompleteHandler),
								('/merchants/mobile/businessdetails',MobileBusinessDetailsHandler),
								('/merchants/mobile/signup',MobileSignupHandler),
								('/merchants/mobile/manage',MobileManageHandler),
								('/merchants/mobile/view',MobileDealViewHandler),
								('/merchants/mobile/deal',MobileDealHandler),
								('/merchants/mobile/deal/create',MobileDealCreateHandler),
								('/merchants/mobile/deal/edit',MobileDealEditHandler),
								('/merchants/mobile/deal/photorotate',MobilePhotoRotateHandler),
								('/merchants/mobile/deal/photoserve/(.*)',MobilePhotoServeHandler),
								('/merchants/mobile/deal/expire',MobileDealExpireHandler),
								('/merchants/mobile/deal/reanimate',MobileDealReanimateHandler),
								('/merchants/mobile/photo',MobilePhotoHandler),
								('/merchants/mobile/photo/create',MobilePhotoCreateHandler),
								('/merchants/mobile/photo/edit',MobilePhotoEditHandler),
								('/merchants/mobile/dealtext/create',MobileDealTextCreateHandler),
								('/merchants/mobile/dealtext/edit',MobileDealTextEditHandler),
								('/merchants/mobile/description/create',MobileDescriptionCreateHandler),
								('/merchants/mobile/description/edit',MobileDescriptionEditHandler),
								('/merchants', MerchantsHandler),
								('/merchants/', MerchantsHandler),
								('/merchants/beta', MerchantsBetaHandler),
								('/merchants/betaRequest', MerchantsBetaRequestHandler),
								('/merchants/login', LoginHandler),
								('/merchants/logout', LogoutHandler),
								('/merchants/password/lost', LostPasswordHandler),
								('/merchants/password/reset', ResetPasswordHandler),
								('/merchants/emailCheck', EmailCheckHandler),
								('/merchants/welcome', WelcomeHandler),
								('/merchants/deal', DealHandler),
								('/merchants/deal/upload', DealUploadHandler),
								('/merchants/deal/delete/(.*)', DeleteDealHandler),
								('/merchants/deal/reanimate/(.*)', ReanimateDealHandler),
								('/merchants/edit.*', EditDealHandler),
								('/merchants/deal/update', DealUpdateHandler),
								('/merchants/editDeal/upload', EditDealUploadHandler),
								('/merchants/verify', VerifyHandler),
								('/merchants/verify/call', VerifyCallHandler),
								('/merchants/verify/answer', VerifyAnswerHandler),
								('/merchants/verify/statusCallback', VerifyStatusCallbackHandler),
								('/merchants/manage', ManageHandler),
								('/merchants/upload', UploadHandler),
								('/merchants/widget', WidgetHandler),
								('/merchants/myAccount', MyAccountHandler),
								('/merchants/myAccount/checkPassword', CheckPasswordHandler)
								], debug=True)
