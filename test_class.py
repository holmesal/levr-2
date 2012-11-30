#from __future__ import with_statement
from datetime import datetime #@UnusedImport
from google.appengine.api import images, urlfetch, files, taskqueue #@UnusedImport
from google.appengine.ext import blobstore, db
from google.appengine.ext.webapp import blobstore_handlers
import api_utils
import api_utils_social as social
import jinja2
import json #@UnusedImport
import levr_classes as levr
import levr_encrypt as enc
import logging
import os
import webapp2

class SandboxHandler(api_utils.BaseHandler):
	'''
	Dont delete this. This is my dev playground.
	'''
	def say(self,stuff):
		self.response.out.write(stuff)
	def get(self):
		'''
		
		'''
		self.response.headers['Content-Type'] = 'text/plain'
		# SPOOF
		query = 'Food'
		deals = []
		tags = ['drink','coffe','lunch','appet','bar','drink','tip']
		for t in tags:
			deals.extend(levr.Deal.all().filter('tags',t).fetch(None))
		deals = list(set(deals))
		self.response.out.write('\n\t\t\t<===================>\n'.join([levr.log_model_props(deal, ['deal_text','description']) for deal in deals]))
#		deal.tags = ['tagggg']
		# /SPOOF
#		assert False, deals
#		parent_tags = levr.tagger(query)
#		for deal in deals:
#			Linker.register_categorization(deal, parent_tags)
#		for deal in deals:
#			Linker.register_deal_click(deal, query)
		for deal in deals:
			api_utils.KWLinker.register_like(deal, query)
		self.response.out.write('\n\nDone!')
		
	def get_foursquare_deals(self):
		'''
		For debugging. Creates a bunch of foursquare deals, and stores them on the server
		'''
		self.response.headers['Content-Type'] = 'text/plain'
		users = levr.Customer.all().fetch(None)
		geo_point = levr.geo_converter('42.343880,-71.059570')
		token = 'IDMTODCAKR34GOI5MSLEQ1IWDJA5SYU0PGHT4F5CAIMPR4CR'
		deal_status = levr.DEAL_STATUS_ACTIVE
		foursquare_ids = []
		
		new_foursquare_deals = api_utils.search_foursquare(geo_point,token,deal_status,foursquare_ids)
		
		self.say(new_foursquare_deals)
class TestNotificationHandler(api_utils.BaseHandler):
	def get(self):
		# aliases cus im laaaaazy
		say = self.response.out.write
		log = levr.log_model_props
		note = levr.Notification
		
		self.response.headers['Content-Type'] = 'text/plain'
		
		to_be_notified = db.get(db.Key.from_path('Customer','pat'))
		actor = db.get(db.Key.from_path('Customer','alonso'))
		deal = levr.Deal.all().get()
		
		notifications = [
				note().radius_alert(to_be_notified, deal),
				note().good_taste_alert(to_be_notified, deal),
				note().previous_like(to_be_notified, deal),
				note().new_follower(to_be_notified, actor),
				note().following_upload(to_be_notified, actor, deal),
				note().upvote(to_be_notified, actor, deal)
				]
		
		
		
		self.response.out.write('<=====================>')
		packaged_notes = api_utils.package_notification_multi(notifications)
		say('\n\t\t<=====================>\n'.join([levr.log_dict(p) for p in packaged_notes]))
		
		
		
class CombineNinjaOwnership(api_utils.BaseHandler):
	def get(self):
		'''
		Grabs all of the deals at a business, and sets all of the deals to the same ninja owner
		'''
		assert False, 'You shouldnt be here. this handler is dangerous unless used wisely'
		self.response.headers['Content-Type'] = 'text/plain'
		# change ownership of rednecks roast beef deals
		
		deals = levr.Deal.all(
							).filter('businessID','ahRkZXZ-bGV2ci1kZXZlbG9wbWVudHIPCxIIQnVzaW5lc3MY2AIM' # test - berklee boloco
#							).filter('businessID','ahFzfmxldnItcHJvZHVjdGlvbnIQCxIIQnVzaW5lc3MY2-wKDA' # Rednecks
							).filter('deal_status','test'
							).fetch(None)
		for deal in deals:
			self.response.out.write(levr.log_model_props(deal,['deal_text','deal_status']))
			self.response.out.write(deal.parent_key())
		levr.Deal.properties()
		ninja = api_utils.get_random_dead_ninja()
		self.response.out.write('\n\n'+str(ninja.key())) # ahRkZXZ-bGV2ci1kZXZlbG9wbWVudHIPCxIIQ3VzdG9tZXIY8wEM
		new_deals = []
		for deal in deals:
			new_deal = levr.Deal(parent=ninja)
			for prop in deal.properties():
				if prop[0] != '_':
					val = getattr(deal, prop)
					setattr(new_deal, prop, val)
			
			new_deals.append(new_deal)
			# expire the old deal
#			self.response.out.write(levr.log_model_props(new_deal))
			self.response.out.write('\n')
			self.response.out.write(levr.log_model_props(deal) == levr.log_model_props(new_deal))
			self.response.out.write('\n')
			deal.expire()
		
		# compile into one list
		deals.extend(new_deals)
		db.put(deals)
		for deal in deals:
			self.response.out.write(levr.log_model_props(deal,['deal_text','deal_status']))
			self.response.out.write(deal.parent_key())
		self.response.out.write('\n\ndone!')
		
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
		
		
		
#		ethan = pat = alonso = ninja = False
		# new customer
		ethan = levr.Customer.all(keys_only=True).filter('email','ethan@levr.com').get()
		levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
		if not ethan:
			ethan = levr.Customer(levr_token = levr_token,key_name = 'ethan')
			ethan.email	= 'ethan@levr.com'
			ethan.pw 	= enc.encrypt_password('ethan')
			ethan.alias	= 'ethan owns the deals'
			ethan.display_name = 'Ethans S.'
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
			pat = levr.Customer(levr_token = levr_token, key_name = 'pat')
			pat.email	= 'patrick@levr.com'
			pat.pw 	= enc.encrypt_password('patrick')
			pat.alias	= 'patrick'
			pat.display_name = 'Patricks W.'
			pat.favorites	= []
			pat.tester = True
			pat.levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
#			pat.foursquare_id = 22161113
			pat.foursquare_token = 'ML4L1LW3SO0SKUXLKWMMBTSOWIUZ34NOTWTWRW41D0ANDBAX'
#			pat.twitter_friends_by_sn = ['LevrDevr']
			pat = pat.put()
		
		
		alonso = levr.Customer.all(keys_only=True).filter('email','alonso@levr.com').get()
		if not alonso:
			alonso = levr.Customer(levr_token = levr_token,key_name = 'alonso')
			alonso.email	= 'alonso@levr.com'
			alonso.pw 	= enc.encrypt_password('alonso')
			alonso.alias	= 'alonso'
			alonso.display_name = 'Alonsos H.'
			alonso.favorites	= []
#			alonso.foursquare_token = '4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0'
			alonso.tester = True
			
			alonso.levr_token = 'tlvXNw9F5Qgnqm_uKxYUx9xeyJHSRDnfBbVmUwvDWzQ'
#			alonso.foursquare_id = 32773785
			alonso.foursquare_token = 'RGTMFLSGVHNMZMYKSMW4HYFNEE0ZRA5PTD4NJE34RHUOQ5LZ'
			
			alonso = alonso.put()
		
		ninja = levr.Customer.all(keys_only=True).filter('email','santa@levr.com').get()
		if not ninja:
			ninja = levr.Customer(levr_token = levr_token, key_name = 'ninja')
			ninja.email	= 'santa@levr.com'
			ninja.pw 	= enc.encrypt_password('santa')
			ninja.alias	= 'Followed'
			ninja.display_name = 'Ninja F.'
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
		
		deal = levr.dealCreate(params,'phone_new_business')
		p = db.get(pat)
		p.upvotes.append(deal.key())
		p.put()
		params = {
					'uid'				: ethan,
					'business_name'		: 'Als Sweatshop',
					'geo_point'			: levr.geo_converter('42.343880,-71.059575'),
					'vicinity'			: '10 Buick St',
					'types'				: 'Establishment,Food',
					'deal_description'	: 'This is a description gut guts who why when you buy a shoe with feet',
					'deal_line1'		: 'I am a deal',
					'distance'			: '10', #is -1 if unknown = double
					'development'		: True,
					'img_key'			: img_key
					}
		
		deal = levr.dealCreate(params,'phone_new_business')
		
		bus = levr.Business.gql('WHERE business_name=:1','Als Sweatshop').get()
		
		ant = levr.Customer.get(ethan)
		
		ant.owner_of = str(bus.key())
		ant.put()
		a = db.get(alonso)
		a.upvotes.append(deal.key())
		a.put()
		
		
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
#		projection = [
#					'alias',
#					'new_notifications',
#					'first_name',
#					'last_name',
#					'karma',
#					'level',
#					'display_name',
#					'followers',
#					
#					'foursquare_id',
#					'foursquare_token',
#					'foursquare_connected',
#					'foursquare_friends',
#					
#					'twitter_id',
#					'twitter_token',
#					'twitter_token_secret',
#					'twitter_screen_name',
#					'twitter_connected',
#					'twitter_friends_by_sn',
#					'twitter_friends_by_id',
#					
#					'facebook_connected',
#					'facebook_token',
#					'facebook_id',
#					'facebook_friends',
#					
#					'email_friends',
#					
#					'favorites',
#					'upvotes',
#					'downvotes',
#					]
		projection = []
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
		
		



FEMALE_EMAIL = 'undeadninja@levr.com'
MALE_EMAIL = 'undeadninja@levr.com'
class Create100DeadNinjasHandler(webapp2.RequestHandler):
	def get(self):
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
		#update photo url, and reference table with photo 
		
		logging.info('Creating 100 dead ninjas.')
		
class CompleteNinjaReferencesHandler(webapp2.RequestHandler):
	def get(self):
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
		pass
		
class RemoveFoursquareHandler(api_utils.BaseHandler):
	def get(self):
		
		t1 = datetime.now()
		deals = levr.Deal.all().filter('origin','foursquare').run(limit=3000,batch_size=500)
		self.response.out.write('\n')
		db.delete(deals)
		self.response.out.write(datetime.now() - t1)
		
class UploadPhotoHandler(webapp2.RequestHandler):
	'''
	Form to upload photos for undead ninjas
	'''
	def get(self):
		
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
		pass
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
		pass


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
		pass
		



app = webapp2.WSGIApplication([('/new', MainPage),
								('/new/upload', DatabaseUploadHandler),
								('/new/test', TestHandler),
								('/new/deadNinjas', Create100DeadNinjasHandler),
								('/new/deadNinjas/complete',CompleteNinjaReferencesHandler),
								('/new/sandbox', SandboxHandler),
								('/new/upload_ninjas',UploadPhotoHandler),
								('/new/store_upload', StorePhotoHandler),
								('/new/transfer_deals', TransferDealOwnershipToUndeadHandler),
								('/new/removefs',RemoveFoursquareHandler),
								],debug=True)


