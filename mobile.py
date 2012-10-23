import webapp2
import os
import logging
import jinja2
import json
import levr_classes as levr
import levr_encrypt as enc
from google.appengine.ext import blobstore, db
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import taskqueue
import urllib
import api_utils
import mixpanel_track as mp_track
import time

#create jinja environment
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

def check_user_agent(self):
	uastring = str(self.request.headers['user-agent'])
	
	logging.info(uastring)
		
	if 'iPhone' in uastring:
		return 'ios'
	elif 'iPad' in uastring:
		return 'ios'
	else:
		return 'unknown'
		
	return 'ios'


class MobileDownloadHandler(webapp2.RequestHandler):
	def get(self):
		
		#write out the download page
		template = jinja_environment.get_template('templates/landing_v3.html')
		self.response.out.write(template.render())
		

class MobileUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		
		logging.debug(self.get_uploads())
		if self.get_uploads(): #will this work?
			upload	= self.get_uploads()[0]
			logging.info(upload)
			blob_key= upload.key()
			img_key = blob_key
			upload_flag = True
		else:
			upload_flag = False
			raise KeyError('Image was not uploaded')
		
		uid = enc.decrypt_key(self.request.get('uid'))
		businessID = enc.decrypt_key(self.request.get('businessID'))
		deal_text = self.request.get('deal_text')
		description = self.request.get('description')
		contentID = self.request.get('contentID')
		
		logging.info(uid)
		logging.info(businessID)
		logging.info(deal_text)
		logging.info(description)
		
		business = levr.Business.get(businessID)
		user = levr.Customer.get(uid)
		
		params = {
					'uid'				: user,
					'business_name'		: business.business_name,
					'geo_point'			: business.geo_point,
					'vicinity'			: business.vicinity,
					'types'				: ','.join(map(str, business.types)),	#phone sends in a comma separated string, types is stored as a list
					'deal_description'	: description,
					'deal_line1'		: deal_text,
					'distance'			: -1, #is -1 if unknown = double
					'development'		: False,
					'img_key'			: img_key
					}

		dealID = levr.dealCreate(params,'phone_new_business')
		
		#fire off a task to do the image rotation stuff
		task_params = {
			'blob_key'	:	str(img_key)
		}
		taskqueue.add(url='/tasks/checkImageRotationTask',payload=json.dumps(task_params))
		
		#track event via mixpanel (asynchronous)
		# try:
# 			properties = {
# 				'time'				:	time.time(),
# 				'distinct_id'		:	enc.encrypt_key(user.key()),		
# 				'mp_name_tag'		:	user.display_name
# 			}
# 			mp_track.track('Deal uploaded','ab1137787f393161bd481e2756b77850',properties)
# 			
# 			to_increment = {
# 						"Deals uploaded"	:	1
# 			}
# 			
# 			mp_track.increment(enc.encrypt_key(user.key()),'ab1137787f393161bd481e2756b77850',to_increment)
# 			
# 		except:
# 			levr.log_error()
		
		
		logging.info('/mobile/upload/complete/?uid='+urllib.quote(enc.encrypt_key(uid)))
		self.redirect('/mobile/upload/complete/?uid='+urllib.quote(enc.encrypt_key(uid)))
		
		
class UploadCompleteHandler(webapp2.RequestHandler):
	def get(self,*args,**kwargs):
		
		uid = self.request.get('uid')
		
		template_values = {
			'uid'		: uid,
			'user_agent': check_user_agent(self)
		}
		
		#write out the download page
		template = jinja_environment.get_template('templates/mobileuploadcomplete.html')
		self.response.out.write(template.render(template_values))


class ContentIDHandler(webapp2.RequestHandler):
	def get(self,*args,**kwargs):
		
		try:
			#grab the content ID
			contentID = args[0]
			#contentID = self.request.get('contentID')
			logging.debug('ContentID: ' + contentID)
			
			#uhh wtf do i do?
			floating_content = levr.FloatingContent.gql('WHERE contentID=:1',contentID).get()
				
			logging.info(floating_content.action)
			
			if floating_content.action == 'upload':
				user = floating_content.user
				
				#write out upload template
				template = jinja_environment.get_template('templates/mobileupload.html')
				template_values = {
					'uid':enc.encrypt_key(str(floating_content.user.key())),
					'businessID':enc.encrypt_key(str(floating_content.business.key())),
					'upload_url':blobstore.create_upload_url('/mobile/upload')
				}
				logging.debug(template_values)
				
				# upload_url = blobstore.create_upload_url('/mobile/upload')
# 				
# 				self.response.out.write('<html><body>')
# 				self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
# 				self.response.out.write('Business ID: <input name="businessID" value="%s">' % enc.encrypt_key(str(floating_content.business.key())))
# 				self.response.out.write('uid: <input name="uid" value="%s">' % enc.encrypt_key(str(floating_content.user.key())))
# 				self.response.out.write('''Upload File: <input type="file" name="img"><br> <input type="submit"
# 				name="submit" value="Create!"> </form></body></html>''')
				
			elif floating_content.action == 'deal':
				#write out deal template
				template = jinja_environment.get_template('templates/mobiledealview.html')
				template_values = {
					'uid':enc.encrypt_key(str(floating_content.user.key())),
					'deal':	api_utils.package_deal(floating_content.deal),
					'user_agent': check_user_agent(self)
				}
			
 			self.response.out.write(template.render(template_values))
			
		except:
			levr.log_error()
			
			

app = webapp2.WSGIApplication([('/mobile/download',MobileDownloadHandler),
								('/mobile/upload',MobileUploadHandler),
								('/mobile/upload/complete/(.*)',UploadCompleteHandler),
								('/mobile/(.*)',ContentIDHandler)],debug=True)