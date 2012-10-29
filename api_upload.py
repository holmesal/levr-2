from google.appengine.api import mail, taskqueue
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from tasks import IMAGE_ROTATION_TASK_URL
import api_utils
import json
import levr_classes as levr
import logging
import os
import webapp2
import levr_encrypt as enc
#import geo.geohash as geohash
#from datetime import datetime
#from google.appengine.ext import db
#import json

class UploadRequestHandler(webapp2.RequestHandler):
	'''
	Requests an upload url
	inputs: uid, levr_token
	response: {
		url: str
	}
	'''
	@api_utils.validate(None,'param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			logging.info('fetchUploadURL\n\n\n')
			logging.debug(kwargs)
			user = kwargs.get('user')
			
			#create blobstore user
			upload_url = blobstore.create_upload_url('/api/upload/post')
			logging.debug(upload_url)
			
			
			
			if os.environ['SERVER_SOFTWARE'].startswith('Development') == True:
				#we are on the development environment
				URL = 'http://0.0.0.0:8080/'
			else:
				#we are deployed on the server
				URL = 'levr.com/'
			
			#create share url
			share_url = URL+levr.create_unique_id()
			
			response = {
					'uploadURL'		: upload_url,
					'shareURL'		: share_url
					}
			api_utils.send_response(self,response,user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class UploadPostHandler(blobstore_handlers.BlobstoreUploadHandler):
	'''
	Post a deal
	'''
	@api_utils.validate(None,'param',
					user			= True,
					levrToken		= True,
					businessName	= True,
					geoPoint		= True,
					vicinity		= True,
					types			= True,
					description		= False,
					dealText		= True,
					distance		= True,
					shareURL		= True
					)
	@api_utils.private
	def post(self,*args,**kwargs):
		try:
			logging.info('uploadDeal\n\n\n')
			logging.info(kwargs)
			user = kwargs.get('actor')
			uid = user.key()
			#make sure than an image is uploaded
			logging.debug(self.get_uploads())
			if self.get_uploads(): #will this work?
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
				upload_flag = True
			else:
				upload_flag = False
				raise KeyError('Image was not uploaded')
			
			
			
			params = {
				'uid'				: uid,
				'business_name'		: kwargs.get('businessName'),
				'geo_point'			: kwargs.get('geoPoint'),
				'vicinity'			: kwargs.get('vicinity'),
				'types'				: kwargs.get('types'),
				'deal_description'	: kwargs.get('description'),
				'deal_line1'		: kwargs.get('dealText'),
				'distance'			: kwargs.get('distance'), #is -1 if unknown = double
				'shareURL'			: kwargs.get('shareURL'),
				'development'		: kwargs.get('development'),
				'img_key'			: img_key
				}
			
			#create the deal using the origin specified
			deal_entity = levr.dealCreate(params,'phone_new_business',upload_flag)
			
			#fire off a task to rotate the image
			task_params = {
				'blob_key'	:	str(deal_entity.img.key())
			}
			
			logging.info('Sending this to the task: '+str(task_params))
			
			
			taskqueue.add(url=IMAGE_ROTATION_TASK_URL,payload=json.dumps(task_params))
			
			
			#give the user some karma
			user.karma += 5
			#level check!
			user = api_utils.level_check(user)
			user.put()
			
			#go notify everyone that should be informed
			try:
				levr.create_notification('followedUpload',user.followers,user.key(),deal_entity)
			except:
				levr.log_error()
			
			#grab deal information for sending back to phone
			deal = api_utils.package_deal(deal_entity,True)
			
			response = {
					'deal'	: deal
					}
			
			#===================================================================
			# Send notification to founders
			#===================================================================
			try:
		#		approve_link = 'http://www.levr.com/admin/deal/{}/approve'.format(enc.encrypt_key(deal_entity.key()))
				reject_link = 'http://www.levr.com/admin/deal/{}/reject'.format(enc.encrypt_key(deal_entity.key()))
				
#				message = mail.EmailMessage()
#				message.to = ['patrick@levr.com','alonso@levr.com']
				message = mail.AdminEmailMessage()
				message.sender = 'patrick@levr.com'
				message.subject = 'New Upload'
				
				message.html = '<img src="{}"><br>'.format(deal.get('smallImg'))
				message.html += '<h2>{}</h2>'.format(deal_entity.deal_text)
				message.html += '<h3>{}</h3>'.format(deal_entity.description)
				message.html += '<p>Uploaded by: {}</p>'.format(user.display_name)
				message.html += '<p>deal_status: {}</p>'.format(deal_entity.deal_status)
				message.html += '<br>Reject: {}<br><br>'.format(reject_link)
				message.html += levr.log_dict(deal, None, '<br>')
				
		#		message.body += '\n\n\n\n\n\nApprove: {}'.format(approve_link)
				
				message.check_initialized()
				message.send()
				
				
#				message = mail.EmailMessage()
#				message.to = ['patrick@levr.com']
##				message = mail.AdminEmailMessage()
#				message.sender = 'new_deal@levr.com'
#				message.subject = 'This is awkward but... you have a new upload'
#				
#				
#				message.body = levr.log_dict(deal)
#				message.check_initialized()
#				message.send()
			except:
				levr.log_error()
			
			api_utils.send_response(self,response)
		
		except KeyError,e:
			levr.log_error()
			api_utils.send_error(self,str(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
		
app = webapp2.WSGIApplication([('/api/upload/request', UploadRequestHandler),
								('/api/upload/post', UploadPostHandler)
								],debug=True)