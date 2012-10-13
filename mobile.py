import webapp2
import os
import logging
import jinja2
import levr_classes as levr
import levr_encrypt as enc
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import urllib

#create jinja environment
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MobileDownloadHandler(webapp2.RequestHandler):
	def get(self):
		
		#write out the download page
		template = jinja_environment.get_template('templates/landing_v3.html')
		self.response.out.write(template.render())
		

class MobileUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self,*args,**kwargs):
		
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
		callback_url = self.request.get('callback_url')
		
		logging.info(uid)
		logging.info(businessID)
		logging.info(deal_text)
		logging.info(description)
		logging.info(callback_url)
		
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
		
		self.redirect('/mobile/upload/complete/?callback_url='+urllib.quote(callback_url))
		
class UploadCompleteHandler(webapp2.RequestHandler):
	def get(self,*args,**kwargs):
		
		#check if phone is iphone or android
		download_url = 'http://www.google.com'
		
		callback_url = self.request.get('callback_url')
		
		template_values = {
			'download_url'	:	download_url,
			'callback_url'	:	callback_url
		}
		
		#write out the download page
		template = jinja_environment.get_template('templates/mobileUploadComplete.html')
		self.response.out.write(template.render(template_values))
		


class ContentIDHandler(webapp2.RequestHandler):
	def get(self,*args,**kwargs):
		
		try:
			#grab the content ID
			contentID = args[0]
			logging.debug('ContentID: ' + contentID)
			callback_url = self.request.get('fsqCallback')
			
			#uhh wtf do i do?
			floating_content = levr.FloatingContent.gql('WHERE contentID=:1',contentID).get()
				
			logging.info(floating_content.action)
			
			if floating_content.action == 'upload':
				user = floating_content.user
				
				#create upload url
				upload_url = blobstore.create_upload_url('/mobile/upload')
				
				#write out upload template
				template = jinja_environment.get_template('templates/mobileupload.html')
				template_values = {
					'uid':enc.encrypt_key(str(floating_content.user.key())),
					'businessID':enc.encrypt_key(str(floating_content.business.key())),
					'upload_url':upload_url,
					'callback_url':callback_url
				}
			elif floating_content.action == 'deal':
				#write out deal template
				template = jinja_environment.get_template('templates/landing_v3.html')
				template_values = {}
				
				
			
			self.response.out.write(template.render(template_values))
			
		except:
			levr.log_error()
			
			

app = webapp2.WSGIApplication([('/mobile/download',MobileDownloadHandler),
								('/mobile/upload',MobileUploadHandler),
								('/mobile/upload/complete/(.*)',UploadCompleteHandler),

								('/mobile/(.*)',ContentIDHandler)],debug=True)