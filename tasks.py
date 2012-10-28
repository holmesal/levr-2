from datetime import datetime
from google.appengine.api import urlfetch
from google.appengine.ext import db, blobstore
import api_utils
import base64
import json
import levr_classes as levr
import logging
import urllib
import webapp2
from google.appengine.api import images
from google.appengine.api import files
#import levr_encrypt as enc
#import api_utils_social as social


class SearchFoursquareTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
				
				THE FOURSQUARE DEAL SEARCH TASK IS RUNNING
				
				''')
			
			
			
#  			logging.debug(self.request.body)
			payload = json.loads(self.request.body)
# 			logging.debug(payload)
			geo_point = db.GeoPt(payload['lat'],payload['lon'])
# 			logging.info(geo_point)
			foursquare_ids = payload['foursquare_ids']
# 			logging.info(foursquare_ids)
			#grab the token from the payload
			token = payload['token']
#			logging.info(token)
			deal_status = payload.get('deal_status','active')
# 			logging.info(levr.log_model_props(user))
			
			#foursquare stuff!
			ft1 = datetime.now()
#			logging.info('FOURSQUARE IDS::::')
#			logging.info(foursquare_ids)
#			logging.debug('searching foursquare () from a task!')
			foursquare_deals = api_utils.search_foursquare(geo_point,token,deal_status,foursquare_ids)
			logging.info('Foursquare results found: '+str(len(foursquare_deals)))
#			logging.info('Duplicates not put in database: '+str(len(foursquare_ids)))
			ft2 = datetime.now()
			logging.info('Foursquare action time: ' + str(ft2-ft1))
			
			
		except:
			levr.log_error()
			
class BusinessHarmonizationTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
			
			THE FOURSQUARE BUSINESS TASK IS RUNNING
			
			''')
			
			payload = json.loads(self.request.body)
			logging.debug(payload)
			
			geo_point = levr.geo_converter(payload['geo_str'])
			
			query = payload['query']
			
			key = payload['key']
			
			match = api_utils.match_foursquare_business(geo_point,query)
	
			logging.info(match)
			
			business = levr.Business.get(key)
			
			if match:
				logging.info('Foursquare ID found: '+match['foursquare_id'])
				
				#are there any previously added foursquare businesses?
				#q_orphans = levr.Business.gql('WHERE foursquare_id=:1',match['foursquare_id'])
				
				#grab a duplicate business
				duplicate_business = levr.Business.gql('WHERE foursquare_id=:1',match['foursquare_id']).get()
				
				keys = []
				if duplicate_business:
					#grab all the deal keys from that business
					keys = levr.Deal.gql('WHERE businessID = :1',str(duplicate_business.key())).fetch(None,keys_only=True)
					duplicate_business.delete()
					logging.debug('DELETED ORIGINAL FOURSQUARE BUSINESS')
				
				#update business entity
				business.foursquare_id = match['foursquare_id']
				business.foursquare_name = match['foursquare_name']
				business.foursquare_linked	=	True
				business.put()
				
				for key in keys:
					deal = db.get(key)
					deal.businessID = str(business.key())
					deal.put()
					logging.debug('UPDATED DEAL BUSINESSID')
				
			else:
				#update to show notfound
				logging.info('No foursquare match found.')
				
				
			#go grab all the deals and update
			
		except:
			levr.log_error()
				
class FoursquareDealUpdateTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
			
			THE FOURSQUARE DEAL UPDATE TASK IS RUNNING
			
			''')
			
			payload = json.loads(self.request.body)
			
			foursquare_id = payload['foursquare_id']
			deal_id = payload['deal_id']
			uid = payload['uid']
			token =  payload['token']
			deal_status = payload['deal_status']
			
			logging.info('This task was started by a user/deal with the following information:')
			logging.info('UID: '+uid)
			logging.info('Foursquare user token: '+token)
			logging.info('Reported deal ID: '+deal_id)	
			logging.info('Business foursquare ID: '+foursquare_id)
			logging.info('deal_status: '+deal_status)
			
			api_utils.update_foursquare_business(foursquare_id,deal_status,token)
			
			
		except:
			levr.log_error()
				
class NewUserTextTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			
			logging.info('''
				
				SKYNET IS TEXTING THE FOUNDERS
				
				''')
			
			payload = json.loads(self.request.body)
			
			#twilio credentials
			sid = 'AC4880dbd1ff355288728be2c5f5f7406b'
			token = 'ea7cce49e3bb805b04d00f76253f9f2b'
			twiliourl='https://api.twilio.com/2010-04-01/Accounts/AC4880dbd1ff355288728be2c5f5f7406b/SMS/Messages.json'
			
			auth_header = 'Basic '+base64.b64encode(sid+':'+token)
			logging.info(auth_header)
			
			numbers = ['+16052610083','+16035605655']
			
			for number in numbers:
				request = {'From':'+16173608582',
							'To':number,
							'Body':'Awwwww yeeeaahhhhh. You have a new user: '+payload['user_string']}
			
			result = urlfetch.fetch(url=twiliourl,
								payload=urllib.urlencode(request),
								method=urlfetch.POST,
								headers={'Authorization':auth_header})
								
			logging.info(levr.log_dict(result.__dict__))
			
		except:
			levr.log_error()
			
class MergeUsersTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			
			logging.info('''
				
				THE MERGE USERS TASK IS RUNNING
				
				''')
			
			payload = json.loads(self.request.body)
			
			uid = payload['uid']
			contentID = payload['contentID']
			service = payload['service']
			
			#grab the user
			user = levr.Customer.get(uid)
			#grab the donor's foursquare token
			floating_content = levr.FloatingContent.gql('WHERE contentID=:1',contentID).get()
			donor = floating_content.user
			
			api_utils.merge_customer_info_from_B_into_A(user,donor,service)
			
		except:
			levr.log_error()
			
class RotateImageHandler(webapp2.RequestHandler):
	def post(self):
		'''This should be called after an image is uploaded from a source where an ipad or iphone might have been used to add an image inside a web wrapper'''
		
		logging.info('''
				
				THE ROTATE IMAGE TASK IS RUNNING
				
				''')
		
		payload = json.loads(self.request.body)
			
		blob_key = payload['blob_key']
			
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
				new_blob_key = files.blobstore.get_blob_key(overwrite)
				
				#grab the reference to the old image
				deal = levr.Deal.gql('WHERE img=:1',blob_key).get()
				logging.debug('Old img key: '+blob_key)
				logging.debug('New img key: '+str(new_blob_key))
				deal.img = new_blob_key
				logging.debug(deal.img)
				deal.put()
				logging.debug('Deal updated')
				
				#delete the old blob
				blob.delete()
				logging.debug('Old image deleted successfully')
			else:
				logging.info('Image oriented properly')
		else:
			logging.info('No "Orientation" property found in Exif data - this image must have been rotated previously')
			
		
class ClearOldNinjasHandler(webapp2.RequestHandler):
	def post(self):
#		self.response.headers['Content-Type'] = 'text/plain'
#		self.response.out.write('Start\n')
		old_ninjas = levr.Customer.all().filter('email','undeadninja@levr.com').fetch(None)
		
		all_content = set([])
#		to_save = set([])
#		users = set([])
		for ninja in old_ninjas:
			# to delete
			floating_content 	= ninja.floating_content.fetch(None)
			notes 				= levr.Notification.all().filter('actor',ninja).fetch(None)
			notes2 				= levr.Notification.all().filter('to_be_notified',ninja.key()).fetch(None)
			deals				= levr.Deal.all().ancestor(ninja).fetch(None)
			
			# failsafe
			# to remove references
			following			= ninja.following.fetch(None)
			for user in following:
				user.followers.remove(ninja.key())
			
			
			
			all_content.update(floating_content)
			all_content.update(notes)
			all_content.update(notes2)
			all_content.update(deals)
			
			for deal in deals:
				# failsafe
				owner = deal.key().parent()
				try:
					owner = db.get(owner)
				except:
					owner = owner
				assert owner.display_name != 'Carl D.'
				assert owner.display_name != 'Patch W.'
				#to delete
				notes3 = deal.notifications.fetch(None)
				floating_content1 = deal.floating_content.fetch(None)
				
				all_content.update(notes3)
				all_content.update(floating_content1)
				
#				#to remove reference
#				favs = levr.Customer.all().filter('favorites',deal.key())
#				upvotes = levr.Customer.all().filter('upvotes',deal.key())
#				downvotes = levr.Customer.all().filter('downvotes',deal.key())
#				
#				
#				users.update(favs)
#				users.update(upvotes)
#				users.update(downvotes)
				
				# remove user references to deals
#				for user in users:
#					try:
#						user.favorites.remove(deal.key())
#					except:
#						pass
#					try:
#						user.upvotes.remove(deal.key())
#					except:
#						pass
#					try:
#						user.downvotes.remove(deal.key())
#					except:
#						pass
				
			# remove user references to other users
#			for user in users:
#				try:
#					user.followers.remove(ninja.key())
#				except:
#					pass
#			
#			to_save.update(users)
		
#		for user in to_save:
#			logging.info(levr.log_model_props(user, ['display_name'])+'\n')
		all_content.update(old_ninjas)
		for i in all_content:
			logging.info(str(i)+'\n')
		
		
#		to_save = list(to_save)
		all_content = list(all_content)
		
#		logging.debug(to_save.__len__())
#		c = 300
#		if to_save.__len__() > 400:
#			logging.debug('length too long: '+str(to_save.__len__()))
#			to_save1 = to_save[:c]
#			to_save2 = to_save[c:]
#			db.put(to_save1)
#			db.put(to_save2)
##		if to_save2.__len__() > 400:
##			to_save3 = to_save2[:c]
##			to_save4 = to_save2[c:]
#		else:
#			db.put(to_save)
			
			
		c = 100
		if all_content.__len__() > c:
			logging.debug('length too long: '+str(all_content.__len__()))
			all_content1 = all_content[:c]
			all_content2 = all_content[c:c*2]
			all_content3 = all_content[c*2:c*3]
			all_content4 = all_content[c*3:c*4]
			all_content5 = all_content[c*4:]
			db.delete(all_content1)
			db.delete(all_content2)
			db.delete(all_content3)
			db.delete(all_content4)
			db.delete(all_content5)
		else:
			db.delete(all_content)
		logging.info('done!')
IMAGE_ROTATION_TASK_URL = '/tasks/checkImageRotationTask'
app = webapp2.WSGIApplication([('/tasks/searchFoursquareTask', SearchFoursquareTaskHandler),
								('/tasks/businessHarmonizationTask', BusinessHarmonizationTaskHandler),
								('/tasks/foursquareDealUpdateTask', FoursquareDealUpdateTaskHandler),
								('/tasks/newUserTextTask', NewUserTextTaskHandler),
								('/tasks/mergeUsersTask', MergeUsersTaskHandler),
								(IMAGE_ROTATION_TASK_URL, RotateImageHandler),
								('/tasks/clearOldNinjas', ClearOldNinjasHandler)
								],debug=True)