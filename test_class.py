#from __future__ import with_statement
#from google.appengine.api import files
from datetime import datetime #@UnusedImport
from google.appengine.api import images, urlfetch, files, taskqueue #@UnusedImport
from google.appengine.ext import blobstore, db
from google.appengine.ext.webapp import blobstore_handlers
import api_utils
import json #@UnusedImport
import levr_classes as levr
import levr_encrypt as enc
import logging
import webapp2
import jinja2
import os
from google.appengine.api import mail
#import api_utils
#import json
#from google.appengine.api import taskqueue, urlfetch, memcache
#from random import randint
#import api_utils_social
#import base_62_converter as converter
#import geo.geohash as geohash
#import uuid
#import geo.geohash as geohash


class MainPage(webapp2.RequestHandler):
	def get(self):
		logging.info('hello'+'\xe9')
		refresh = self.request.get('refresh',False)
		if refresh:
			self.response.out.write('<b>THIS WILL RESET THE DB. SET REFRESH=FALSE</b><br/>')
			upload_url = blobstore.create_upload_url('/new/upload?refresh=True')
		else:
			upload_url = blobstore.create_upload_url('/new/upload')
		logging.info('!!!')
		logging.info(upload_url)
		# The method must be "POST" and enctype must be set to "multipart/form-data".
		self.response.out.write('<html><body>')
		self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
		self.response.out.write('''Upload File: <input type="file" name="img"><br> <input type="submit"
		name="submit" value="Create!"> </form></body></html>''')

class DatabaseUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		#get uploaded image
		upload = self.get_uploads()[0]
#		upload = self.request.get('img')
#		upload = blobstore.Blob(upload)
		blob_key= upload.key()
		img_key = blob_key
		logging.info(upload)
		
		refresh = self.request.get('refresh',False)
		if refresh:
			entities = levr.Customer.all(keys_only=True).filter('tester',True).fetch(None)
			notes = []
			for e in entities:
				notes += levr.Notification.all(keys_only=True).filter('actor',e).fetch(None)
				
			entities += notes
			
			entities += levr.Deal.all(keys_only=True).filter('deal_status','test').fetch(None)
			
			db.delete(entities)
		
#		ethan = pat = alonso = ninja = False
		# new customer
		ethan = levr.Customer.all(keys_only=True).filter('email','ethan@levr.com').get()
		levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
		if not ethan:
			ethan = levr.Customer(levr_token = levr_token)
			ethan.email	= 'ethan@levr.com'
			ethan.pw 	= enc.encrypt_password('ethan')
			ethan.alias	= 'ethan owns the deals'
			ethan.favorites	= []
			ethan.tester = True
			ethan.levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
#			ethan.foursquare_id = 37756769
			ethan.foursquare_token = 'IDMTODCAKR34GOI5MSLEQ1IWDJA5SYU0PGHT4F5CAIMPR4CR'
#			ethan.twitter_token = '819972614-2HoAwfJcHCOePogonjPbNNxuQQsvHeYeJ3U2KasI'
			ethan.twitter_screen_name = 'LevrDevr'
			ethan.twitter_id	= 819972614
			ethan = ethan.put()
		'AAACEdEose0cBANvf0FVOdH0NpoqLDZCnt8ZAlVfiYqe90CH1S7rOAEZC7ZChI340ElsX0bYXXOZC1Ks1kWU4JmsGMpUWzp7fm6CfIHKdXwN4ZAvVCFfGMa'
		pat = levr.Customer.all(keys_only=True).filter('email','patrick@levr.com').get()
		if not pat:
			pat = levr.Customer(levr_token = levr_token)
			pat.email	= 'patrick@levr.com'
			pat.pw 	= enc.encrypt_password('patrick')
			pat.alias	= 'patrick'
			pat.favorites	= []
			pat.tester = True
			pat.levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
#			pat.foursquare_id = 22161113
			pat.foursquare_token = 'ML4L1LW3SO0SKUXLKWMMBTSOWIUZ34NOTWTWRW41D0ANDBAX'
#			pat.twitter_friends_by_sn = ['LevrDevr']
			pat = pat.put()
		
		
		alonso = levr.Customer.all(keys_only=True).filter('email','alonso@levr.com').get()
		if not alonso:
			alonso = levr.Customer(levr_token = levr_token)
			alonso.email	= 'alonso@levr.com'
			alonso.pw 	= enc.encrypt_password('alonso')
			alonso.alias	= 'alonso'
			alonso.favorites	= []
#			alonso.foursquare_token = '4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0'
			alonso.tester = True
			
			alonso.levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
#			alonso.foursquare_id = 32773785
			alonso.foursquare_token = 'RGTMFLSGVHNMZMYKSMW4HYFNEE0ZRA5PTD4NJE34RHUOQ5LZ'
			
			alonso = alonso.put()
		
		ninja = levr.Customer.all(keys_only=True).filter('email','santa@levr.com').get()
		if not ninja:
			ninja = levr.Customer(levr_token = levr_token)
			ninja.email	= 'santa@levr.com'
			ninja.pw 	= enc.encrypt_password('santa')
			ninja.alias	= 'Followed'
			ninja.favorites = []
			ninja.tester = True
			ninja.levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
			ninja = ninja.put()
			
			
		
		
		
		params = {
					'uid'				: ethan,
					'business_name'		: 'Als Sweatshop',
					'geo_point'			: levr.geo_converter('42.343880,-71.059570'),
					'vicinity'			: '10 Buick St',
					'types'				: 'Establishment,Food',
					'deal_description'	: 'This is a description gut guts who why when you buy a shoe with feet',
					'deal_line1'		: 'I am a deal',
					'distance'			: '10', #is -1 if unknown = double
					'development'		: True,
					'img_key'			: img_key
					}

		levr.dealCreate(params,'phone_new_business')
		
		params = {
					'uid'				: ethan,
					'business_name'		: 'Als Sweatshop 2',
					'geo_point'			: levr.geo_converter('42.343879999999999, -71.059569999999994'),
					'vicinity'			: '10 Buick St',
					'types'				: 'Establishment,Food',
					'deal_description'	: 'This is a description gut guts who why when you buy a shoe with feet',
					'deal_line1'		: 'I am a deal',
					'distance'			: '10', #is -1 if unknown = double
					'development'		: True,
					'img_key'			: img_key
					}
		
		levr.dealCreate(params,'phone_new_business')
		
		params = {
					'uid'				: ethan,
					'business_name'		: 'Als Sweatshop 3',
					'geo_point'			: levr.geo_converter('42.343880,-71.059575'),
					'vicinity'			: '10 Buick St',
					'types'				: 'Establishment,Food',
					'deal_description'	: 'This is a description gut guts who why when you buy a shoe with feet',
					'deal_line1'		: 'I am a deal',
					'distance'			: '10', #is -1 if unknown = double
					'development'		: True,
					'img_key'			: img_key
					}
		
		levr.dealCreate(params,'phone_new_business')
		
		bus = levr.Business.gql('WHERE business_name=:1','Als Sweatshop').get()
		
		ant = levr.Customer.get(alonso)
		
		ant.owner_of = str(bus.key())
		ant.put()
		
		
		
		
		self.redirect('/new/test')

class TestHandler(webapp2.RequestHandler):
	def get(self):
		
		e = levr.Customer.all().filter('email','ethan@levr.com').get()
		ethan = enc.encrypt_key(e.key())
		p = levr.Customer.all().filter('email','patrick@levr.com').get()
		pat = enc.encrypt_key(p.key())
		a = levr.Customer.all().filter('email','alonso@levr.com').get()
		alonso = enc.encrypt_key(a.key())
		n = levr.Customer.all().filter('email','santa@levr.com').get()
		ninja = enc.encrypt_key(n.key())
		
		
		
		url = '\'http://0.0.0.0:8080/api'
		
		
		ethan_url = url+'/user/'+ethan+'\' | python -mjson.tool'
		pat_url = url+'/user/'+pat+'\' | python -mjson.tool'
		alonso_url = url+'/user/'+alonso+'\' | python -mjson.tool'
		ninja_url = url+'/user/'+ninja+'\' | python -mjson.tool'
		
		
		levr_token = db.get(enc.decrypt_key(ethan)).levr_token
		self.response.out.headers['Content-Type'] = 'text/plain'
		self.response.out.write('LEVR TOKEN:\n\n')
		self.response.out.write(levr_token)
		self.response.out.write('\n\n\nFor ethan:\n\n')
		self.response.out.write(ethan)
		self.response.out.write('\n\n')
		self.response.out.write('curl '+ethan_url)
		
		self.response.out.write('\n\n\nFor pat:\n\n')
		self.response.out.write(pat)
		self.response.out.write('\n\n')
		self.response.out.write('curl '+pat_url)
		
		self.response.out.write('\n\n\n<b>For alonso: </b>\n\n')
		self.response.out.write(alonso)
		self.response.out.write('\n\n')
		self.response.out.write('curl '+alonso_url)
		
		self.response.out.write('\n\n\n<b>For ninja: </b>\n\n')
		self.response.out.write(ninja)
		self.response.out.write('\n\n')
		self.response.out.write('curl '+ninja_url)
		
		d = levr.Deal.all().ancestor(db.Key(enc.decrypt_key(ethan))).get()
		if d:
			deal = enc.encrypt_key(d.key())
			deal_url = url+'/deal/'+deal+'\' | python -mjson.tool'
		
			self.response.out.write('\n\n\n<b>For deal stuff: </b>\n\n')
			self.response.out.write(deal)
			self.response.out.write('\n\n')
	#		self.response.out.write('\n\n')
			self.response.out.write('curl '+deal_url)
		
#		projection = None
		projection = [
					'alias',
					'new_notifications',
					'first_name',
					'last_name',
					'karma',
					'level',
					'display_name',
					'followers',
					
					'foursquare_id',
					'foursquare_token',
					'foursquare_connected',
					'foursquare_friends',
					
					'twitter_id',
					'twitter_token',
					'twitter_token_secret',
					'twitter_screen_name',
					'twitter_connected',
					'twitter_friends_by_sn',
					'twitter_friends_by_id',
					
					'facebook_connected',
					'facebook_token',
					'facebook_id',
					'facebook_friends',
					
					'email_friends',
					
					'favorites',
					'upvotes',
					'downvotes',
					]
		deal_projection = [
						'upvotes',
						'downvotes',
						'karma',
						'geo_point',
						'geo_hash'
						]
		self.response.out.write('\n\n\n Ethan')
		self.response.out.write(levr.log_model_props(e,projection))
		self.response.out.write('\n PAT')
		self.response.out.write(levr.log_model_props(p,projection))
		self.response.out.write('\n ALONSO')
		self.response.out.write(levr.log_model_props(a,projection))
		self.response.out.write('\nDEAL')
		if d: self.response.out.write(levr.log_model_props(d,deal_projection))
		self.response.out.write('\n\n')
		notifications = levr.Notification.all().fetch(None)
		for n in notifications:
			self.response.out.write(levr.log_model_props(n))
		
		
	
		
class AddDealsHandler(webapp2.RequestHandler):
	def get(self):
		
		lons = [x/1000. for x in range(72400,72600,10) if x%5 ==0]
		lats = [x/1000. for x in range(42400,42600,10) if x%5 ==0]
		self.response.out.write(lons.__len__()*lats.__len__())
		self.response.out.write(lats)
		
		
#		ethan = levr.Customer.all().filter('email','ethan@levr.com').get().key()
#		
#		for lat in lats:
#			for lon in lons:
#				
#				params = {
#							'uid'				: ethan,
#							'business_name'		: 'Als Sweatshop',
#							'geo_point'			: levr.geo_converter(str(lat)+','+str(lon)),
#							'vicinity'			: '10 Buick St',
#							'types'				: 'Establishment,Food',
#							'deal_description'	: 'This is a description',
#							'deal_line1'		: 'I am a deal',
#							'distance'			: '10', #is -1 if unknown = double
#	#						'img_key'			: img_key
#							}
#		
#				dealID = levr.dealCreate(params,'phone_new_business',False)
#				self.response.out.write(dealID)
#		pass
		self.response.out.write('<br>Done')
	

class TestNotificationHandler(webapp2.RequestHandler):
	def get(self):
		
		logging.info('WTFFFF')
		logging.debug('HOLY SHIT NEW NOTIFICATIONS OMG OMG OMG')
		
		#go get the ninja
		user = levr.Customer.gql('WHERE email=:1','q').get()
		#go get the user
		actor = levr.Customer.gql('WHERE email=:1','alonso@levr.com').get()
		#go get the deal
		deal = levr.Deal.all().ancestor(user.key()).get()
		
		if not deal:
			deal = levr.Deal.all().get()
		
		assert deal, 'Cannot find any deals. Try uploading one. If that doesnt work, abandon all hope.' 
		
		#new follower notification
		levr.create_notification('newFollower',user.key(),actor)
		
		#followed upload notification
		levr.create_notification('followedUpload',user.key(),actor,deal.key())
		
		#favorite notification
		levr.create_notification('favorite',user.key(),actor,deal.key())
		
		#levelup notification
		user.new_notifications += 1
		levr.create_notification('levelup',user.key(),actor,new_level='inf')
		user.put()
		self.response.out.write('HOLY SHIT NEW NOTIFICATIONS OMG OMG OMG')


FEMALE_EMAIL = 'deadninja2@levr.com'
MALE_EMAIL = 'deadninja1@levr.com'
class Create100DeadNinjasHandler(webapp2.RequestHandler):
	def get(self):
		
		logging.info('Creating 100 dead ninjas.')
		
#		#=======================================================================
#		# Males
#		#=======================================================================
#		f1 = open('male_undead_ninjas.txt')
#		males = f1.read().split('\n')
#		
#		projection = ['display_name','alias','email']
#		
#		undead_males = []
#		for name in males:
#			first_name = name.split(' ')[0]
#			last_name = name.split(' ')[1]
#			display_name = first_name+' '+last_name[0]+'.'
#			
#			ninja = levr.Customer(
#					display_name 		=	display_name,
#					alias				=	display_name,
#					email				=	MALE_EMAIL,
#					first_name			=	first_name,
#					last_name			=	last_name,
#					foursquare_token	=	'4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0',
#					pw					=	enc.encrypt_password('iamnotaninja'),
#					levr_token			=	levr.create_levr_token()
#				)
#			
#			
#			logging.info(levr.log_model_props(ninja,projection))
#			undead_males.append(ninja)
#		
#		
#		#=======================================================================
#		# Females
#		#=======================================================================
#		f2 = open('female_undead_ninjas.txt')
#		females = f2.read().split('\n')
#		
#		
#		
#		
#		undead_females = []
#		for name in females:
#			first_name = name.split(' ')[0]
#			last_name = name.split(' ')[1]
#			display_name = first_name+' '+last_name[0]+'.'
#			
#			ninja = levr.Customer(
#					display_name 		=	display_name,
#					alias				=	display_name,
#					email				=	FEMALE_EMAIL,
#					first_name			=	first_name,
#					last_name			=	last_name,
#					foursquare_token	=	'4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0',
#					pw					=	enc.encrypt_password('iamnotaninja'),
#					levr_token			=	levr.create_levr_token()
#				)
#			
#			
#			logging.info(levr.log_model_props(ninja,projection))
#			undead_females.append(ninja)
#		
#		#=======================================================================
#		# Place ninjas
#		#=======================================================================
#		all_ninjas = []
#		for n in undead_males:
#			all_ninjas.append(n)
#		for n in undead_females:
#			all_ninjas.append(n)
#		db.put(all_ninjas)
#		self.response.out.write(all_ninjas.__len__())
#		#update photo url, and reference table with photo 
#		
		
class CompleteNinjaReferencesHandler(webapp2.RequestHandler):
	def get(self):
		pass
#		host_url = api_utils.host_url
#		hook = 'api/user/'
#		size = 'small'
#		
#		self.response.headers['Content-Type'] = 'text/plain'
#		
#		undead_males = levr.Customer.all().filter('email',MALE_EMAIL).fetch(None)
#		logging.debug(undead_males)
#		male_photos = levr.UndeadNinjaBlobImgInfo.all().filter('gender','male').fetch(None)
#		logging.debug(male_photos)
#		#update photo url, and reference table with photo 
#		for idx,ninja in enumerate(undead_males):
#			#update users photourl
#			
#			img_url = host_url+hook+enc.encrypt_key(ninja.key())+'/img?size='+size
#			self.response.out.write(img_url)
#			ninja.photo = img_url
#			
#			#update relational db
#			photo_info = male_photos[idx]
#			photo_info.ninja = ninja
#		
#		
#		
#		undead_females = levr.Customer.all().filter('email',FEMALE_EMAIL).fetch(None)
#		logging.debug(undead_females)
#		female_photos = levr.UndeadNinjaBlobImgInfo.all().filter('gender','female').fetch(None)
#		female_photos.extend(levr.UndeadNinjaBlobImgInfo.all().filter('gender','either').fetch(None))
#		logging.debug(female_photos)
#		
#		for idx,ninja in enumerate(undead_females):
#			#update users photourl
#			img_url = host_url+hook+enc.encrypt_key(ninja.key())+'/img?size='+size
#			self.response.out.write(img_url)
#			ninja.photo = img_url
#			
#			#update relational db
#			photo_info = female_photos[idx]
#			photo_info.ninja = ninja
#		
#		
#		all_ninjas = []
#		for female in undead_females:
#			all_ninjas.append(female)
#		for male in undead_males:
#			all_ninjas.append(male)
#		
#		all_img_objs = []
#		for p in female_photos:
#			all_img_objs.append(p)
#		for p in male_photos:
#			all_img_objs.append(p)
#			
#		
##		db.put(all_ninjas)
##		db.put(all_img_objs)
#		
#		all_objs = []
#		for i in all_ninjas:
#			all_objs.append(i)
#		for i in all_img_objs:
#			all_objs.append(i)
#		
#		db.put(all_objs)
#		
#		projection = ['display_name','email']
#		
#		self.response.headers['Content-Type'] = 'text/plain'
#		for user in all_ninjas:
#			self.response.out.write(levr.log_model_props(user,projection))
#		for img in all_img_objs:
#			self.response.out.write(levr.log_model_props(img))

		
class HarmonizeVenuesHandler(webapp2.RequestHandler):
	def get(self):
		pass
#		all_businesses = levr.Business.gql('WHERE foursquare_name = :1','notfound')
		
		# for business in all_businesses:
# 			logging.info('launching task for business: ' + business.business_name)
# 			task_params = {
# 			'geo_str'		:	str(business.geo_point),
# 			'query'			:	business.business_name,
# 			'key'			:	str(business.key())
# 			}
# 			
# 			t = taskqueue.add(url='/tasks/businessHarmonizationTask',payload=json.dumps(task_params))


		
class SandboxHandler(webapp2.RequestHandler):
	'''
	Dont delete this. This is my dev playground.
	'''
	def get(self):
#		self.response.headers['Content-Type'] = 'text/plain'
		deal_entity = levr.Deal.all().filter('origin','levr').filter('deal_status','test').get()
		logging.debug(deal_entity.key())
		logging.debug(deal_entity.deal_text)
		user = db.get(deal_entity.parent_key())
		
		deal = api_utils.package_deal(deal_entity, True)
		
		reject_link = 'http://www.levr.com/admin/deal/{}/reject'.format(enc.encrypt_key(deal_entity.key()))
		message = mail.EmailMessage()
		message.to = ['patrick@levr.com']
#		message = mail.AdminEmailMessage()
		message.sender = 'patrick@levr.com'
		message.subject = 'New Upload'
		
		message.html = '<img src="{}"><br>'.format(deal.get('smallImg'))
		message.html += '<h1>{}</h1><br>'.format(deal_entity.deal_text)
		message.html += '<h3>{}</h3><br>'.format(deal_entity.description)
		message.html += '<h4>Uploaded by: {}</h4>'.format(user.display_name)
		message.html += '<p>deal_status: {}</p>'.format(deal_entity.deal_status)
		message.html += '<br><br><br>Reject: {}<br><br><br>'.format(reject_link)
		message.html += levr.log_dict(deal, None, '<br>')
		
#		message.body += '\n\n\n\n\n\nApprove: {}'.format(approve_link)
		
		message.check_initialized()
		message.send()
		self.response.out.write(message.html)
class UploadPhotoHandler(webapp2.RequestHandler):
	'''
	Form to upload photos for undead ninjas
	'''
	def get(self):
		pass
#		upload_url = blobstore.create_upload_url('/new/store_upload')
#		self.response.out.write('<html><body>')
#		self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
##		self.response.out.write('<input type="file" id="file_input" webkitdirectory="" directory="">')
#		self.response.out.write('''
#		Gender: <br/>
#		<input type="radio" name="gender" value="male">Male
#		<br/>
#		<input type="radio" name="gender" value="female">Female
#		<br/>
#		<input type="radio" name="gender" value="either">Either
#		<br/>
#		''')
#		for i in range(0,50):
#			self.response.out.write('Upload File: <input type="file" name="img'+str(i)+'"><br>')
#		self.response.out.write(''' <input type="submit" name="submit" value="Create!"> </form></body></html>''')

class StorePhotoHandler(blobstore_handlers.BlobstoreUploadHandler):
	'''
	Stores a photo to the blobstore to be used as an undead ninja photo
	'''
	def post(self):
		pass
#		#get uploaded image
##		logging.info(levr.log_dir(self.request))
#		#list of 100 uploads
#		uploads = self.get_uploads()
#		gender = self.request.get('gender')
#		self.response.out.write(uploads)
#		blob_keys = [u.key() for u in uploads]
#		imgs = []
#		for key in blob_keys:
#			imgs.append(levr.UndeadNinjaBlobImgInfo(
#													img = key,
#													gender = gender
#													))
#			self.response.out.write(str(key)+'<br/>')
#		db.put(imgs)
#		self.response.out.write(blob_keys)



class ClearOldNinjasHandler(webapp2.RequestHandler):
	'''
	Used to do two things BECAUSE I AM LAZY OK?! First section clears out the old ninjas and their tendrils,
	second section resets all of the new ninjas emails to undeadninja@levr.com instead of undeadninja1 and 2 (for gender)
	'''
	def get(self):
		pass
##		taskqueue.add(url='/tasks/clearOldNinjas',payload=json.dumps({}))
##		self.response.out.write('done!')





##		ninjas = levr.Customer.all().filter('email',levr.UNDEAD_NINJA_EMAIL).fetch()
#		ninjas = levr.Customer.all().filter('email',FEMALE_EMAIL).fetch(None)
#		ninjas2 = levr.Customer.all().filter('email', MALE_EMAIL).fetch(None)
#		
#		all_ninjas = set([])
#		for ninja in ninjas:
#			n = [ninja]
#			all_ninjas.update(n)
#		for ninja in ninjas2:
#			n = [ninja]
#			all_ninjas.update(n)
#		
#		all_ninjas = list(all_ninjas)
#		for ninja in all_ninjas:
#			ninja.email = levr.UNDEAD_NINJA_EMAIL
#		
#		db.put(all_ninjas)
#		self.response.out.write('done!')
class TransferDealOwnershipToUndeadHandler(webapp2.RedirectHandler):
	def get(self):
		pass
#		# Fetch all deals uploaded by pat and alonso the other day
#		alonso = levr.Customer.all().filter('display_name','Carl D.').get()
#		assert alonso ,'Alonso is not there!'
#		deals = levr.Deal.all().ancestor(alonso).fetch(None)
#		assert deals.__len__() >0,'No alonso deals.'
#		
#		pat = levr.Customer.all().filter('display_name','Patrick W.').get()
#		assert pat, 'No Pat!'
#		pat_deals = levr.Deal.all().ancestor(pat).fetch(None)
#		assert pat_deals.__len__()>0, 'No pat deals'
#		
#		#one long list of deals
#		deals.extend(pat_deals)
#		
#		# each ninja has uploaded two deals
#		num = deals.__len__()/2
#		ninjas = api_utils.get_random_dead_ninja(num)
#		ninjas.extend(ninjas)
#		
#		assert ninjas.__len__() == deals.__len__(), 'Array lengths are not equal'
#		
#		new_deals = set([])
#		for idx, deal in enumerate(deals):
#			# create new deal as child of a ninja
#			ninja = ninjas[idx]
#			new_deal = levr.Deal(parent = ninja)
#			
#			# iterate through properties and set them to the new_deal
#			properties = filter(lambda x: x[0] != '_',deal.properties())
#			
#			logging.debug(properties)
#			for prop in properties:
#				value = getattr(deal, prop)
#				setattr(new_deal, prop, value)
#			
#			assert levr.log_model_props(new_deal) == levr.log_model_props(deal), 'Deals are not equal'
#			
#			# add deal to list of new deals
#			new_deals.update([new_deal])
#			
#			#set old deal to expired
#			deal.deal_status = 'expired'
#			new_deals.update([deal])
#		# finish
#		db.put(new_deals)
		

class LandingTestHandler(webapp2.RequestHandler):
	def get(self):
		
		#grab all the deals (for now)
		# deal_q = levr.Deal.all(keys_only=True).filter('origin','levr')
# 		deal_keys = deal_q.fetch(50)
# 		deals = db.get(deal_keys)
		
		#TODO: grab deals from a few specific geohashes that cover boston
		geo_hash_set = ['drt3','drmr','drt8','drt0','drt1','drt9','drmx','drmp','drt2']
		
		logging.debug('\n\n\n \t\t\t START QUERYING \n\n\n')
		query_start = datetime.now()
		deal_keys = api_utils.get_deal_keys(geo_hash_set)
		query_end = datetime.now()
		
		total_query_time = query_end-query_start
		
		logging.debug('\n\n\n \t\t\t END QUERYING \n\n\n ')
		
		logging.info('Query time: '+str(total_query_time))
		
		deals = db.get(deal_keys)
		
		sorted_deals = []
		#remove the non-active and foursquare deals
		for deal in deals:
			logging.debug(deal.deal_status)
			if deal.deal_status in ['active','test']:
				logging.debug(deal.origin)
				if deal.origin in ['levr','merchant']:
					sorted_deals.append(deal)
				else:
					logging.info('deal not added because origin was: '+deal.origin)
			else:
				logging.info('deal not added because status was:' +deal.deal_status)
		
		packaged_deals = api_utils.package_deal_multi(sorted_deals)
		
# 		logging.info(packaged_deals)
		
		#go through and swap lat and lon
		for deal in packaged_deals:
			logging.info(deals)
			#separate lat and lon
			deal['lat'] = deal['business']['geoPoint'].split(',')[0]
			deal['lon'] = deal['business']['geoPoint'].split(',')[1]
			#fix image url
			deal['imgURL'] = deal['largeImg'].split('?')[0]+'?size=webMapView'
		

		template_values = {
			'deals'		: packaged_deals,
			'version'	: 'desktop'
		}
		
		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/landing_v4.html')
		self.response.out.write(template.render(template_values))


app = webapp2.WSGIApplication([('/new', MainPage),
								('/new/upload', DatabaseUploadHandler),
								('/new/test', TestHandler),
								('/new/inundate', AddDealsHandler),
								('/new/notification', TestNotificationHandler),
								('/new/deadNinjas', Create100DeadNinjasHandler),
								('/new/deadNinjas/complete',CompleteNinjaReferencesHandler),
								('/new/harmonizeVenues',HarmonizeVenuesHandler),
								('/new/sandbox', SandboxHandler),
								('/new/upload_ninjas',UploadPhotoHandler),
								('/new/store_upload', StorePhotoHandler),
								('/new/clear_old_ninjas', ClearOldNinjasHandler),
								('/new/transfer_deals', TransferDealOwnershipToUndeadHandler),
								('/new/landing', LandingTestHandler)
								],debug=True)


