#from __future__ import with_statement
#from google.appengine.api import files
from datetime import datetime
from google.appengine.api import images, urlfetch, files
from google.appengine.ext import blobstore, db
from google.appengine.ext.webapp import blobstore_handlers
import levr_classes as levr
import levr_encrypt as enc
import logging
import webapp2
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
		
		dealID = levr.dealCreate(params,'phone_new_business')
		
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
			
class Create100DeadNinjasHandler(webapp2.RequestHandler):
	def get(self):
		logging.info('Creating 100 dead ninjas.')
		
		dead_ninjas = ['Jack Walsh','Jeffrey Kiggins','Elisabeth Austin','Robert Bailey','Nikole Bakopolus','Paul Barry','Will Burnham','Paul Callahan','Izona Fripp','John Glavin','Frank Gatheral','Robert Glasberg','Richard Golden','John Guilderson','John Hagan','Ann Hensey','Patrick Higgins','Alan Hilsinger','Hazel Horn','Iris Howard','Specer Hurtt','Marie Karahalis','Jackie Kelleher','Rich Kraska','Kenneth Lowry','Dan Lucas','Rich Luccio','Kathleen MacGillvray','James Palleschi','Sam Payson','Natalie Rosendorf','Sonia Sahagian','James Sharkey','Mary Sousa','Tony Spadofora','Brian Welch','Victor Ferra','Jesus Fojo','Frank Wood','Evelyn Thomas','Jimmy Babcock','Lynn Clark','Kara Gayer','Kevin Hill','James Holley','Chris Jaquex','Erica Lee','Sophia Pisanos','Dorothy Ralph','Josephine Robeson','Stuart Shore','Ted Young','Vivian Zuest','Leonel Escobar','Fran Jacobs','Toshiko Matoba','Sofiya Milman','Carl Niizawa','Angelo Pappas','Isabel Shibuya','Danny Ventura','Lisa Appleberry-Vining','Jake Bodden','John Bosch','Leah Bourgeois','Ben Goodman','Rita Hoizenthal','Brian Hilkirk','Sidney Kornick','Hal LeBlanc','Charles Lemon','Ben Dover','Alvin Rhodes','Julie Strength','Ted Staton','Rob Tricou','Tyler Wehr','Rob White','Carol Wikerson-Johnson','Alice Pilgrim']
		
		undead_ninjas = []
		
		for name in dead_ninjas:
			ninja = levr.Customer(
					display_name 		=	name,
					alias				=	name,
					email				=	'deadninja@levr.com',
					first_name			=	name.split()[0],
					last_name			=	name.split()[1],
					foursquare_token	=	'4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0',
					pw					=	enc.encrypt_password('Carl123!'),
					levr_token			=	levr.create_levr_token()
				)
			
			logging.info(levr.log_model_props(ninja))
			undead_ninjas.append(ninja)
			
		logging.info(undead_ninjas)
		db.put(undead_ninjas)
		
		
#		ninjas = levr.Customer.all().filter('first_name','Dead Ninja').count()
#		#don't want a bagillion dead ninjas by accident do we?
#		if ninjas <100:
#			for number in list(xrange(100)):
#				ninja = levr.Customer(
#					display_name 		=	'Dead Ninja '+str(number),
#					alias				=	'deadninja'+str(number),
#					email				=	'deadninja@levr.com',
#					first_name			=	'Dead Ninja',
#					last_name			=	str(number),
#					foursquare_token	=	'4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0',
#					pw					=	enc.encrypt_password('Carl123!'),
#					levr_token			=	levr.create_levr_token()
#				)
#				
#				ninja.put()
#			self.response.out.write('Done')
#		else:
#			self.response.out.write('Already have 100 undead ninjas')
#		
		#=======================================================================
		# Real undead ninja names'n'shit'stuff yeah
		#=======================================================================
		#make sure this script is only run once
	# 	existing_ninjas = levr.Customer.all().filter('email','deadninja@levr.com').count()
# 		assert existing_ninjas == 0, 'This script has already been run.'
# 		
# 		f	= open('undead_ninja_names.txt','r')
# #		
# 		#read whole text file
# 		conglomerate	= f.read()
# 		logging.debug(conglomerate)
# 		#split into name entries
# 		names_list	= conglomerate.split('\n')
# 		#only take 100 ninjas
# 		if names_list.__len__() >100:
# 			names_list = names_list[:100]
# 		
# 		undead_ninjas = []
# 		for full_name in names_list:
# 			#parse first and last names
# 			first_name, last_name = full_name.split(' ')
# 			#build display name
# 			display_name = '{} {}.'.format(first_name,last_name[0])
# 			ninja = levr.Customer(
# 					display_name 		=	display_name,
# 					alias				=	display_name,
# 					email				=	'deadninja@levr.com',
# 					first_name			=	first_name,
# 					last_name			=	last_name,
# 					foursquare_token	=	'4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0',
# 					pw					=	enc.encrypt_password('Carl123!'),
# 					levr_token			=	levr.create_levr_token()
# 				)
# 			undead_ninjas.append(ninja)
# 		
# 		#sanity check
# 		self.response.out.headers['Content-Type'] = 'text/plain'
# 		self.response.out.write('{} undead ninjas'.format(undead_ninjas.__len__()))
# 		for ninja in undead_ninjas:
# 			self.response.out.write(levr.log_model_props(ninja,['first_name','last_name','display_name']))
# 		
# 		#put all the ninjas
# 		db.put(undead_ninjas)
# 		#how to get a random dead ninja
		#ninja = api_utils.get_random_dead_ninja()
		
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


class RefreshQHandler(webapp2.RequestHandler):
	def get(self):
		q = levr.Customer.all().filter('email','ethan@levr.com').get()
		assert q, 'Could not fetch q...'
		q.favorites = []
		q.upvotes = []
		q.downvotes = []
		q.new_notifications = 0
		q.put()
		self.response.out.write('reset q favroites, upvotes, downvotes')
		
		notifications = levr.Notification.all().ancestor(q.key()).fetch(None)
		
		db.delete(notifications)
		
		self.response.out.write('deleted qs notifications')
		
		self.response.out.write('Done.')
class TestCronJobHandler(webapp2.RequestHandler):
	def get(self):
		try:
			self.response.out.headers['Content-Type'] = 'text/plain'
			self.response.out.write('Hello\n')
			
			now = datetime.now()
			
			### DEBUG
			all_deals = levr.Deal.all().fetch(None)
			for deal in all_deals:
				self.response.out.write(levr.log_model_props(deal,['date_end','deal_status']))
				self.response.out.write(deal.date_end > now)
			### /DEBUG
			
			#fetch all deals that are set to expire
			
			self.response.out.write('\n\n\t\tdate_end: '+str(now))
			deals = levr.Deal.all().filter('deal_status','test').filter('date_end <=',now).fetch(None)
			self.response.out.write('\n\n deals found: '+str(deals.__len__()))
			
			#set deal_status to expired
			for deal in deals:
				
				self.response.out.write(levr.log_model_props(deal))
				deal.deal_status = 'expired'
				to_be_notified = deal.key().parent()
				assert to_be_notified,'No deal parent was found'
				levr.create_notification('expired',to_be_notified,None,deal.key())
			#create notification for ninja owner - epired deal notification
			#fetch parents
			db.put(deals)
			notifications = levr.Notification.all().filter('notification_type','expired').fetch(None)
			for notification in notifications:
				self.response.out.write(levr.log_model_props(notification))
			
		except:
			levr.log_error()
		
class FloatingContentHandler(webapp2.RequestHandler):
	def get(self):
		
		#make up some floating content
		
# 		#delete donor if exists
# 		don = levr.Customer.gql('WHERE alias=:1','donor')
# 		
# 		for d in don:
# 			d.delete()
# 		
# 		#make a new user that is associated with foursquare and nothing else
# 		donor = levr.Customer(
# 				foursquare_token = '4PNJWJM0CAJ4XISEYR4PWS1DUVGD0MKFDMC4ODL3XGU115G0',
# 				alias = 'donor',
# 				levr_token = levr.create_levr_token()
# 		)
# 		
# 		donor.put()
		
		owner = levr.Customer.gql('WHERE email=:1','alonso@levr.com').get()
		assert owner, 'no owner'
		deal = levr.Deal.all().get()#.get('ahFzfmxldnItcHJvZHVjdGlvbnIbCxIIQ3VzdG9tZXIYsuQDDAsSBERlYWwYtG0M')
		assert deal, 'no deal'
		user = levr.Customer.gql('WHERE email=:1','ethan@levr.com').get()
		assert user, 'no user'
		business = levr.Business.get(deal.businessID)
		assert business, 'no business'


		#floating content for upload
		fc = levr.FloatingContent(
				action='upload',
				contentID=levr.create_content_id('foursquare'),
				user=user,
				business=business
		)
		
		self.response.out.write('<p>Upload: ' + fc.contentID + '\n</p>')
		
		# Floating content for a deal
		fc2 = levr.FloatingContent(
				action='deal',
				contentID=levr.create_content_id('foursquare'),
				user=user,
				deal=deal,
				origin='foursquare',
				business=business
		)
		
		self.response.out.write('<p>Deal: ' + fc2.contentID + '\n</p>')
		
		#put it in!
		fc2.put()
		fc.put()
#		
class SandboxHandler(webapp2.RequestHandler):
	'''
	Dont delete this. This is my dev playground.
	'''
	def get(self):
		pass
class UploadPhotoHandler(webapp2.RequestHandler):
	def get(self):
		logging.info('hello'+'\xe9')
		upload_url = blobstore.create_upload_url('/new/store_upload')
		self.response.out.write('<html><body>')
		self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
		self.response.out.write('<input type="file" id="file_input" webkitdirectory="" directory="">')
#		for i in range(0,100):
#			self.response.out.write('Upload File: <input type="file" name="img'+str(i)+'"><br>')
		self.response.out.write(''' <input type="submit" name="submit" value="Create!"> </form></body></html>''')

class StorePhotoHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		#get uploaded image
		logging.info(levr.log_dir(self.request))
		#list of 100 uploads
		uploads = self.get_uploads()
		self.response.out.write(uploads)
		blob_keys = [u.key() for u in uploads]
		
		for key in blob_keys:
			self.response.out.write(str(key)+'<br/>')
#		upload = self.request.get('img')
#		upload = blobstore.Blob(upload)
#		blob_key= upload.key()
#		img_key = blob_key
#		logging.info(upload)
		
#		self.response.out.write()
		
class DeleteEverythingHandler(webapp2.RequestHandler):
	def get(self):
		self.response.out.write('DELETING EVERYTHING - DANGEROUS!')
		
		
		deals = levr.Deal.all().fetch(None)
		db.delete(deals)
		businesses = levr.Business.all().fetch(None)
		db.delete(businesses)
		
#		users = levr.Customer.all().fetch(None)
#		for user in users:
#			if not user.levr_token:
#				user.levr_token = levr.create_levr_token()
#			user.upvotes = []
#			user.favorites = []
#			user.downvotes = []
#		db.put(users)
#		
#		notes = levr.Notifications.all().fetch(None)
#		db.delete(notes)
#		
#		floatings = levr.FloatingContent.all().fetch(None)
#		db.delete(floatings)
#		
#		reports = levr.ReportedDeal.all().fetch(None)
#		db.delete(reports)

class OwnerOfHandler(webapp2.RequestHandler):
	def get(self):
		alonso = levr.Customer.gql('WHERE email=:1','alonso@levr.com').get()
		business = levr.Business.all().get()
		alonso.owner_of = str(business.key())
		alonso.put()
		
<<<<<<< HEAD
=======
class ExifHandler(webapp2.RequestHandler):
	def get(self,blob_key):
		'''This should be called after an image is uploaded from a source where an ipad or iphone might have been used to add an image inside a web wrapper'''
		
		blob = blobstore.BlobInfo.get(blob_key)
		
		img = images.Image(blob_key=blob_key)
		
		#execute a bullshit transform
		img.rotate(0)
		bullshit = img.execute_transforms(output_encoding=images.JPEG,quality=100,parse_source_metadata=True)
		
		#self.response.headers['Content-Type'] = 'image/jpeg'
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
			
			self.response.out.write(str(blob_key))
		else:
			logging.info('Image oriented properly - not rotating')
			
		
			#write image to output
# 			self.response.headers['Content-Type'] = 'image/jpeg'
# 			self.response.out.write(output_img)
			
			#blob_data = blob_key.open().read()
				
			#pass blob data to the image handler
			#img			= images.Image(blob_data)
			#img			= images.Image(blob)
		
class PreviewHandler(webapp2.RequestHandler):
	def get(self,blob_key):
	
		blob = blobstore.BlobInfo.get(blob_key)
		
		img = images.Image(blob_key=blob_key)
	
		img.resize(width=800, height=1000)
		img.im_feeling_lucky()
		thumbnail = img.execute_transforms(output_encoding=images.JPEG,parse_source_metadata=True)
		
		self.response.headers['Content-Type'] = 'image/jpeg'
		self.response.out.write(thumbnail)
		
	

>>>>>>> 4194612823e30747909e313ea804ea1bd0ef16a6
app = webapp2.WSGIApplication([('/new', MainPage),
								('/new/upload', DatabaseUploadHandler),
								('/new/test', TestHandler),
								('/new/inundate', AddDealsHandler),
								('/new/notification', TestNotificationHandler),
								('/new/deadNinjas', Create100DeadNinjasHandler),
								('/new/harmonizeVenues',HarmonizeVenuesHandler),
								('/new/refreshQ', RefreshQHandler),
								('/new/testcron', TestCronJobHandler),
								('/new/floatingContent', FloatingContentHandler),
								('/new/sandbox', SandboxHandler),
								('/new/deleteeverything',DeleteEverythingHandler),
								('/new/ownerof',OwnerOfHandler),
<<<<<<< HEAD
								('/new/upload_ninjas',UploadPhotoHandler),
								('/new/store_upload', StorePhotoHandler)
=======
								('/new/exif/(.*)',ExifHandler),
								('/new/preview/(.*)',PreviewHandler)
>>>>>>> 4194612823e30747909e313ea804ea1bd0ef16a6
								],debug=True)


