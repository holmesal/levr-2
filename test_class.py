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
import api_utils_social as social

#import api_utils
#import json
#from google.appengine.api import taskqueue, urlfetch, memcache
#from random import randint
#import api_utils_social
#import base_62_converter as converter
#import geo.geohash as geohash
#import uuid
#import geo.geohash as geohash

class SandboxHandler(api_utils.BaseClass):
	'''
	Dont delete this. This is my dev playground.
	'''
	def get(self):
		pass
class CombineNinjaOwnership(api_utils.BaseClass):
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
#		#update photo url, and reference table with photo 
#		
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
		

class ViewFoursquareDealsHandler(api_utils.BaseClass):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		deals = levr.Deal.all().filter('origin','foursquare').filter('deal_status','active').fetch(None)
		logging.info(deals)
		points = []
		for deal in deals:
			points.append((deal.geo_hash,deal))
			
#			self.response.out.write(levr.log_model_props(deal, ['deal_text','foursquare_id']))
		points.sort()
		for p in points:
			self.response.out.write(str(p[0])+ ' '+str(p[1].deal_status) +' '+str(p[1].date_end)+' '+repr(p[1].deal_text) +'\n')
		
#		# expire all the foursquare deals to get rid of the redundant ones
		for deal in deals:
			deal.expire()
		#=======================================================================
		# now = datetime.now()
		#	
		# #fetch all deals that are set to expire
		# deals = levr.Deal.all().filter('deal_status','active').filter('date_end <=',now).filter('date_end !=',None).fetch(None)
		# logging.info('<-- With date_end -->\n\n')
		# for deal in deals:
		#	self.response.out.write(str(deal.date_end)+' --> '+ deal.deal_text+'\n')
		#	
		# 
		# 
		# self.response.out.write('\n\n<-- Without date end -->\n\n')
		# deals2 = levr.Deal.all().filter('deal_status','test').fetch(None)
		# for deal in deals2:
		#	self.response.out.write(str(deal.date_end)+' --> '+ deal.deal_text+ '\n')
		#=======================================================================
		pass
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
		

class LandingTestHandler(webapp2.RequestHandler):
	def get(self):
		
		uastring = str(self.request.headers['user-agent'])
	
		logging.info(uastring)
			
# 		if 'iphone' in uastring.lower():
# 			version = 'iPhone'
# 			logging.debug('Serving mobile version - iPhone')
# 		elif 'android' in uastring.lower():
# 			version = 'android'
# 			logging.debug('Serving mobile version - android')
# 		else:
# 			version = 'desktop'
# 			logging.debug('Serving desktop version')
# 			
# 		#version = 'android'
# 		
# 		#todo: grab deals from a few specific geohashes that cover boston
# 		geo_hash_set = ['drt3','drmr','drt8','drt0','drt1','drt9','drmx','drmp','drt2']
# 		
# 		logging.debug('\n\n\n \t\t\t START QUERYING \n\n\n')
# 		query_start = datetime.now()
# 		deal_keys = api_utils.get_deal_keys(geo_hash_set)
# 		query_end = datetime.now()
# 		
# 		total_query_time = query_end-query_start
# 		
# 		logging.debug('\n\n\n \t\t\t END QUERYING \n\n\n ')
# 		
# 		logging.info('Query time: '+str(total_query_time))
# 		
# 		deals = db.get(deal_keys)
# 		
# 		sorted_deals = []
# 		#remove the non-active and foursquare deals
# 		for deal in deals:
# 			logging.debug(deal.deal_status)
# 			if deal.deal_status in ['active']:
# 				logging.debug(deal.origin)
# 				if deal.origin in ['levr','merchant']:
# 					sorted_deals.append(deal)
# 				else:
# 					logging.info('deal not added because origin was: '+deal.origin)
# 			else:
# 				logging.info('deal not added because status was:' +deal.deal_status)
# 		
# 		packaged_deals = api_utils.package_deal_multi(sorted_deals)
# 		
# # 		logging.info(packaged_deals)
# 		
# 		#go through and swap lat and lon
# 		for deal in packaged_deals:
# 			logging.info(deals)
# 			#separate lat and lon
# 			deal['lat'] = deal['business']['geoPoint'].split(',')[0]
# 			deal['lon'] = deal['business']['geoPoint'].split(',')[1]
# 			#fix image url
# 			deal['imgURL'] = deal['largeImg'].split('?')[0]+'?size=webMapView'
# 		
# 
# 		template_values = {
# 			'deals'		: packaged_deals,
# 			'version'	: version
# 		}
		
		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/landing-merchants-v5.html')
		self.response.out.write(template.render())
		
class DevelopersHandler(webapp2.RequestHandler):
	def get(self):
		
		template_values = {
			'latitude'		:	12345,
			'longitude'		:	67890,
			'origin'		:	'foursquare',
			'type'			:	'business',
			'radius'		:	5,
			'query'			:	'hello',
			'business_id'	:	'businessID'
		}
		
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/developers.html')
		self.response.out.write(template.render(template_values))


app = webapp2.WSGIApplication([('/new', MainPage),
								('/new/upload', DatabaseUploadHandler),
								('/new/test', TestHandler),
								('/new/notification', TestNotificationHandler),
								('/new/deadNinjas', Create100DeadNinjasHandler),
								('/new/deadNinjas/complete',CompleteNinjaReferencesHandler),
								('/new/sandbox', SandboxHandler),
								('/new/viewfs', ViewFoursquareDealsHandler),
								('/new/upload_ninjas',UploadPhotoHandler),
								('/new/store_upload', StorePhotoHandler),
								('/new/transfer_deals', TransferDealOwnershipToUndeadHandler),
								('/new/landing', LandingTestHandler),
								('/new/developers', DevelopersHandler)
								],debug=True)


