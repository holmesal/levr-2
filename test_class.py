#from __future__ import with_statement
#from google.appengine.api import files
import webapp2
import levr_classes as levr
import logging
import levr_encrypt as enc
import base_62_converter as converter
#import geo.geohash as geohash
import geo.geohash as geohash
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from datetime import datetime
from random import randint

class MainPage(webapp2.RequestHandler):
	def get(self):
		logging.info('!!!')
		upload_url = blobstore.create_upload_url('/new/upload')
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
		if not ethan:
			ethan = levr.Customer()
			ethan.email	= 'ethan@levr.com'
			ethan.pw 	= enc.encrypt_password('ethan')
			ethan.alias	= 'Deal Owner'
			ethan.favorites	= []
			ethan = ethan.put()
		
		pat = levr.Customer.all(keys_only=True).filter('email','patrick@levr.com').get()
		if not pat:
			pat = levr.Customer()
			pat.email	= 'patrick@levr.com'
			pat.pw 	= enc.encrypt_password('patrick')
			pat.alias	= 'Redeemer'
			pat.favorites	= []
			pat = pat.put()
		
		alonso = levr.Customer.all(keys_only=True).filter('email','alonso@levr.com').get()
		if not alonso:
			alonso = levr.Customer()
			alonso.email	= 'alonso@levr.com'
			alonso.pw 	= enc.encrypt_password('alonso')
			alonso.alias	= 'Follows patrick and ethan'
			alonso.favorites	= []
			alonso = alonso.put()
		
		ninja = levr.Customer.all(keys_only=True).filter('email','santa@levr.com').get()
		if not ninja:
			ninja = levr.Customer()
			ninja.email	= 'santa@levr.com'
			ninja.pw 	= enc.encrypt_password('santa')
			ninja.alias	= 'Followed'
			ninja.favorites = []
			ninja = ninja.put()
		
		
		
		params = {
					'uid'				: enc.encrypt_key(ethan),
					'business_name'		: 'Als Sweatshop',
					'geo_point'			: '42.5,-72.5',
					'vicinity'			: '10 Buick St',
					'types'				: 'Establishment,Food',
					'deal_description'	: 'This is a description gut guts who why when you buy a shoe with feet',
					'deal_line1'		: 'I am a deal',
					'distance'			: '10', #is -1 if unknown = double
					'img_key'			: img_key
					}

		dealID = levr.dealCreate(params,'phone_new_business')
		dealID = levr.dealCreate(params,'phone_new_business')
		dealID = levr.dealCreate(params,'phone_new_business')
		logging.debug(dealID)
		self.redirect('/new/test')

class TestModel(db.Model):
	date = db.IntegerProperty()
	
class TestHandler(webapp2.RequestHandler):
	def get(self):
		
		ethan = enc.encrypt_key(levr.Customer.all().filter('email','ethan@levr.com').get().key())
		pat = enc.encrypt_key(levr.Customer.all().filter('email','patrick@levr.com').get().key())
		alonso = enc.encrypt_key(levr.Customer.all().filter('email','alonso@levr.com').get().key())
		ninja = enc.encrypt_key(levr.Customer.all().filter('email','santa@levr.com').get().key())
		deal = enc.encrypt_key(levr.Deal.all().ancestor(db.Key(enc.decrypt_key(ethan))).get().key())
		
		url = 'http://0.0.0.0:8080/api'
		
		
		ethan_url = url+'/user/'+ethan
		pat_url = url+'/user/'+pat
		alonso_url = url+'/user/'+alonso
		ninja_url = url+'/user/'+ninja
		deal_url = url+'/deal/'+deal
		
		token = db.get(enc.decrypt_key(ethan)).levr_token
		
		self.response.out.write('<b>For ethan: </b><br/><br/>')
		self.response.out.write(ethan)
		self.response.out.write('<br/><br/>')
		self.response.out.write(db.get(enc.decrypt_key(ethan)).levr_token)
		self.response.out.write('<br/><br/>')
		self.response.out.write('curl '+ethan_url)
		
		self.response.out.write('<br/><br/><br/><b>For pat: </b><br/><br/>')
		self.response.out.write(pat)
		self.response.out.write('<br/><br/>')
		self.response.out.write(db.get(enc.decrypt_key(pat)).levr_token)
		self.response.out.write('<br/><br/>')
		self.response.out.write('curl '+pat_url)
		
		self.response.out.write('<br/><br/><br/><b>For alonso: </b><br/><br/>')
		self.response.out.write(alonso)
		self.response.out.write('<br/><br/>')
		self.response.out.write(db.get(enc.decrypt_key(alonso)).levr_token)
		self.response.out.write('<br/><br/>')
		self.response.out.write('curl '+alonso_url)
		
		self.response.out.write('<br/><br/><br/><b>For ninja: </b><br/><br/>')
		self.response.out.write(ninja)
		self.response.out.write('<br/><br/>')
		self.response.out.write(db.get(enc.decrypt_key(ninja)).levr_token)
		self.response.out.write('<br/><br/>')
		self.response.out.write('curl '+ninja_url)
		
		self.response.out.write('<br/><br/><br/><b>For deal stuff: </b><br/><br/>')
		self.response.out.write(deal)
		self.response.out.write('<br/><br/>')
#		self.response.out.write('<br/><br/>')
		self.response.out.write('curl '+deal_url)
		
		self.response.out.write('<br/><br/>')
		self.response.out.write('<br/><br/>')
		self.response.out.write('token: ')
		self.response.out.write('<br/><br/>')
		self.response.out.write(str(token))
		self.response.out.write('<br/><br/>')
		self.response.out.write(levr.unix_time(datetime.now()))
		self.response.out.write('<br/><br/>')
		self.response.out.write('| python -mjson.tool')
		self.response.out.write('<br/><br/>')
		self.response.out.write('<br/><br/>')
		
		t1 = TestModel(
					date = long(levr.unix_time(datetime.now()))
					).put()
		t2 = TestModel(
					date = long(levr.unix_time(datetime.now()))
					).put()
		
		mod1 = db.get(t1)
		mod2 = db.get(t2)
		self.response.out.write(levr.unix_time(datetime.now()))
		self.response.out.write(long(levr.unix_time(datetime.now())))
		self.response.out.write('<br/><br/>')
		self.response.out.write(mod1.date)
		self.response.out.write('<br/><br/>')
		self.response.out.write(mod2.date)
		
		
		follow = '/follow?followerID='
		redeem = '/redeem?uid='
		
	
		
class AddDealsHandler(webapp2.RequestHandler):
	def get(self):
		
#		lons = [x/1000. for x in range(72400,72600,10) if x%5 ==0]
#		lats = [x/1000. for x in range(42400,42600,10) if x%5 ==0]
#		self.response.out.write(lons.__len__()*lats.__len__())
#		self.response.out.write(lats)
#		
#		ethan = levr.Customer.all().get().key()
#		
#		for lat in lats:
#			for lon in lons:
#				
#				params = {
#							'uid'				: enc.encrypt_key(ethan),
#							'business_name'		: 'Als Sweatshop',
#							'geo_point'			: str(lat)+','+str(lon),
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
		pass
	
	
class FilterGeohashHandler(webapp2.RequestHandler):
	def get(self):
#		#take in geo_point
#		#set radius, expand, get all deals
#		
#		
#		
#		request_point = levr.geo_converter('42.35,-71.110')
#		center_hash = geohash.encode(request_point.lat,request_point.lon,precision=6)
#		all_squares = geohash.expand(center_hash)
#		
#		all = levr.Business.all().count()
#		self.response.out.write(all)
#		self.response.out.write('<br/>')
#		
#		keys = []
#		for query_hash in all_squares:
#			q = levr.Business.all(keys_only=True).filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{")
#			keys.extend(q.fetch(None))
#		
#		self.response.out.write(str(keys.__len__())+"<br/>")
#		
#		#get all deals
#		deals = levr.Business.get(keys)
#		logging.debug(deals)
#		for deal in deals:
#			self.response.out.write(deal.geo_hash+"<br/>")
		pass

class UpdateUsersHandler(webapp2.RequestHandler):
	def get(self):
		try:
			logging.warning('!!!!!!!\n\n\n\n')
#			users = levr.Customer.all().fetch(None)
#			for user in users:
#				
##				user.levr_token = levr.create_levr_token()
#				user.favorites = []
#				user.redemptions = []
#				user.downvotes = []
#				user.followers = []
#			db.put(users)
#			
#			for user in users:
#				self.response.out.write(user.levr_token)
#				self.response.out.write('<br/>')
		except:
			levr.log_error()
		
app = webapp2.WSGIApplication([('/new', MainPage),
								('/new/upload.*', DatabaseUploadHandler),
								('/new/find', FilterGeohashHandler),
								('/new/test', TestHandler),
								('/new/inundate', AddDealsHandler),
								('/new/updateUser', UpdateUsersHandler)
#								('/new/update' , UpdateUsersHandler)
								],debug=True)


