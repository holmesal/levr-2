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
		
		# new customer
#		c = levr.Customer(key='agtkZXZ-Z2V0bGV2cnIOCxIIQ3VzdG9tZXIYEgw')
		c = levr.Customer.all().filter('email','ethan@levr.com').get()
		if not c:
			c = levr.Customer()
			c.email	= 'ethan@levr.com'
			c.payment_email = c.email
			c.pw 	= enc.encrypt_password('ethan')
			c.alias	= 'ethan'
			c.favorites	= []
			c.put()
		c2 = levr.Customer.all().filter('email','patrick@levr.com').get()
		if not c2:
			c2 = levr.Customer()
			c2.email	= 'patrick@levr.com'
			c2.payment_email = c.email
			c2.pw 	= enc.encrypt_password('patrick')
			c2.alias	= 'patrick'
			c2.favorites	= []
			c2.put()
		c3 = levr.Customer.all().filter('email','alonso@levr.com').get()
		if not c3:
			c3 = levr.Customer()
			c3.email	= 'alonso@levr.com'
			c3.payment_email = c.email
			c3.pw 	= enc.encrypt_password('alonso')
			c3.alias	= 'alonso'
			c3.favorites	= []
			c3.put()
		
		#new ninja
#		ninja = levr.Customer(key='agtkZXZ-Z2V0bGV2cnIOCxIIQ3VzdG9tZXIYCww')
		ninja = levr.Customer.all().filter('email','santa@levr.com').get()
		if not ninja:
			ninja = levr.Customer()
			ninja.email	= 'santa@levr.com'
			ninja.payment_email = c.email
			ninja.pw 	= enc.encrypt_password('santa')
			ninja.alias	= 'santa'
			ninja.favorites = []
			ninja.put()
		
		
#		#existing business
#		b = levr.Business.all(keys_only=True).get()
#		
#		
#		params = {
#					'uid'				: enc.encrypt_key(c.key()),
#					'business'			: enc.encrypt_key(str(b)),
#					'deal_description'	: 'description!!!',
#					'deal_line1'		: 'DEAL LINE!',
#					'img_key'			: img_key
#					}
#


		#/existing business
		params = {
					'uid'				: enc.encrypt_key(c.key()),
					'business_name'		: 'Als Sweatshop',
					'geo_point'			: '32,-42',
					'vicinity'			: '10 Buick St',
					'types'				: 'Establishment,Food',
					'deal_description'	: 'This is a description',
					'deal_line1'		: 'I am a deal',
					'distance'			: '10', #is -1 if unknown = double
					'img_key'			: img_key
					}



		(share_url,dealID) = levr.dealCreate(params,'phone_new_business')
		logging.debug(share_url)
		logging.debug(dealID)




		self.response.headers['Content-Type'] = 'text/plain'
#		self.response.out.write('/phone/img?dealID='+enc.encrypt_key(str(c.key()))+"&size=dealDetail")
		self.response.out.write('     I think this means it was a success')
#		self.redirect('/phone/img?dealID='+str(cd.key())+"&size=dealDetail")
		
#class UpdateUsersHandler(webapp2.RequestHandler):
#	def get(self):
#		#query
#		users = levr.Customer.all().fetch(None)
#			
#			
#		for user in users:
#			#generate random number to decide what split test group they are in
#			choice = randint(10,1000)
#			decision = choice%2
#			if decision == 1:
#				group = 'paid'
#			else:
#				group = 'unpaid'
#			logging.debug(levr.log_model_props(user))
#			user.group = group
#			logging.debug(levr.log_model_props(user))
#			
#		db.put(users)
class StoreGeohashHandler(webapp2.RequestHandler):
	def get(self):
		#pull all of the businesses
		#grab each of their geo_points
		#has geo_points into geo_hash
		#store geo_hash
		business_keys	= levr.Deal.all(keys_only=True).fetch(None)
		businesses		= levr.Deal.get(business_keys)
		for b in businesses:
			geo_point	= b.geo_point
			logging.debug(geo_point)
			geo_hash	= geohash.encode(geo_point.lat,geo_point.lon)
			logging.debug(geo_hash)
			b.geo_hash	= geo_hash
#			
		db.put(businesses)
			
@staticmethod
def get_by_geo_box(bot_left,bot_right):
	
	hash_min = geohash.encode(bot_left.lat,bot_left.lon,precision=10)
	hash_max = geohash.encode(top_right.lat,top_right.lon,precision=10)
	
	businesses = levr.Business.all().filter('geo_hash >=',hash_min).filter('geo_hash <=',hash_max).fetch(None)
	logging.debug(businesses.__len__())
	return businesses
	

class FilterGeohashHandler(webapp2.RequestHandler):
	def get(self):
		#take in geo_point
		#set radius, expand, get all deals
		
		
		
		request_point = levr.geo_converter('42.35,-71.110')
		center_hash = geohash.encode(request_point.lat,request_point.lon,precision=6)
		all_squares = geohash.expand(center_hash)
		
		all = levr.Business.all().count()
		self.response.out.write(all)
		self.response.out.write('<br/>')
		
		keys = []
		for query_hash in all_squares:
			q = levr.Business.all(keys_only=True).filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{")
			keys.extend(q.fetch(None))
		
		self.response.out.write(str(keys.__len__())+"<br/>")
		
		#get all deals
		deals = levr.Business.get(keys)
		logging.debug(deals)
		for deal in deals:
			self.response.out.write(deal.geo_hash+"<br/>")
		
		
		
		
#		businesses = get_by_geo_box(bot_left, bot_right)
#		
#		
#		hash_min = geohash.encode(bot_left_lat,bot_left_lon)
#		hash_max = geohash.encode(top_right_lat,top_right_lon)
#		
#		
#		self.response.out.write(hash_min+", "+hash_max+"<br/>")
#		
##		length_degrees = .1
#		
#		self.response.out.write(levr.Business.all().count())
#		self.response.out.write('<br/>')
#		
#		q = levr.Business.all().filter('geo_hash >=',hash_min).filter('geo_hash <=', hash_max)
#		self.response.out.write(q.count())
#		self.response.out.write("<br/>")
#		businesses = q.fetch(None)
#		for b in businesses:
#			self.response.out.write(str(b.geo_hash)+"<br/>")
		
#		self.response.out.write(str(levr.Business.all().count())+"<br/>")
#		geo_hash = geohash.encode(lat,lon)
#		
#		all_squares = geohash.expand(geo_hash)
#		
#		self.response.out.write(geo_hash+"<br/>")
#		
#		self.response.out.write(all_squares)
#		self.response.out.write("<br/>")
#		businesses = []
#		count = 0
#		for query_hash in all_squares:
#			q = levr.Business.all().filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{")
#			c = q.count()
#			self.response.out.write(str(c)+"<br/>")
#			count += c
#			bs = q.fetch(None)
#			
#			businesses.extend(bs)
#		self.response.out.write(str(count)+"<br/>")
#		for b in businesses:
#			self.response.out.write(b.geo_hash+"<br/>")
#			self.response.out.write(str(geohash.decode(b.geo_hash))+"<br/>")
			
			
			
			
#		query = levr.Business.all().filter('geo_hash >=',geo_hash).filter('geo_hash <=', geo_hash+"{")
#		count = query.count()
#		self.response.out.write(count)
#		self.response.out.write('<br/>')
#		businesses = query.fetch(None)
#		for b in businesses:
#			self.response.out.write(b.geo_hash)
#			self.response.out.write('<br/>')

class Cust(db.Model):
#root class
	email 			= db.EmailProperty()
	pw 				= db.StringProperty()

class Note(db.Model):
	date			= db.DateTimeProperty(auto_now_add=True)
	notification_type = db.StringProperty(required=True,choices=set(['redemption','thanks','friendUpload','newFollower']))
	user			= db.ReferenceProperty(Cust,collection_name='notifications',required=True)

class TestHandler(webapp2.RequestHandler):
	def get(self):
#		customer = Cust(
#						email	= 'patrick@levr.com',
#						pw		= 'patrick').put()
#		customer
#		
#		#create notifications
#		n1 = Note(
#						notification_type = 'redemption',
#						user = customer
#						).put()
#		n2 = Note(
#						notification_type = 'thanks',
#						user = customer
#						).put()
#		self.response.out.write(customer)
#		#start the fun
		
		#get customer
		customer = Cust.all().get()
		
		logging.info(levr.log_dict(customer.properties()))
		logging.info(customer.notifications.fetch(None))
		n = customer.notifications.filter('notification_type =','redemption').get()
		logging.debug(n.user.email)
		
		
app = webapp2.WSGIApplication([('/new', MainPage),
								('/new/upload.*', DatabaseUploadHandler),
								('/new/geohash', StoreGeohashHandler),
								('/new/find', FilterGeohashHandler),
								('/new/test', TestHandler)
#								('/new/update' , UpdateUsersHandler)
								],debug=True)


