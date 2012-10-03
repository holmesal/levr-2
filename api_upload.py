import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
import geo.geohash as geohash
from datetime import datetime
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


def authorize(handler_method):
	'''
	Decorator checks the privacy level of the request.
	If the uid is valid and the user exists, it checks the levr_token to  privacy level
	
	'''
	def check(self,*args,**kwargs):
		try:
			logging.debug('AUTHORIZE DECORATOR\n\n\n')
#			logging.debug(levr.log_dir(self.request))
			logging.debug(args)
			logging.debug(kwargs)
			
			#CHECK USER
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid','key',True):
				raise Exception('uid: '+str(uid))
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			
			#GET ENTITIES
			user = db.get(uid)
			if not user or user.kind() != 'Customer':
				raise Exception('uid: '+str(uid))
			
			levr_token = self.request.get('levrToken')
			
			#if the levr_token matches up, then private request, otherwise public
			if user.levr_token == levr_token:
				private = True
			else:
				private = False
			
			logging.debug(private)
			
			
			kwargs.update({
						'user'	: user,
						'private': private
						})
		except Exception,e:
			api_utils.send_error(self,'Invalid uid, '+str(e))
		else:
			handler_method(self,*args,**kwargs)
	
	return check

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
			
			response = {
					'url' : upload_url
					}
			api_utils.send_response(self,response,user)
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')
class UploadPostHandler(blobstore_handlers.BlobstoreUploadHandler):
	'''
	Post a deal - does not need special permissions because the upload url expires
	'''
	@api_utils.validate(None,None,
					user			= True,
					businessName	= True,
					geoPoint		= True,
					vicinity		= True,
					types			= True,
					description		= True,
					dealText		= True,
					distance		= True,
					)
	def post(self,*args,**kwargs):
		try:
			logging.info('uploadDeal\n\n\n')
			logging.debug(kwargs)
			user = kwargs.get('actor')
			uid = user.key()
			#make sure than an image is uploaded
			logging.debug(self.get_uploads())
			if self.get_uploads(): #will this work?
				upload	= self.get_uploads()[0]
				blob_key= upload.key()
				img_key = blob_key
			else:
				pass#raise Exception('Image was not uploaded')
			
			
			
			params = {
				'uid'				: uid,
				'business_name'		: kwargs.get('businessName'),
				'geo_point'			: kwargs.get('geoPoint'),
				'vicinity'			: kwargs.get('vicinity'),
				'types'				: kwargs.get('types'),
				'deal_description'	: kwargs.get('description'),
				'deal_line1'		: kwargs.get('dealText'),
				'distance'			: kwargs.get('distance'), #is -1 if unknown = double
#				'img_key'			: img_key
				}
		
			#create the deal using the origin specified
			deal_entity = levr.dealCreate(params,'phone_new_business',False)
			
			#grab deal information for sending back to phone
			deal = api_utils.package_deal(deal_entity,True)
			
			response = {
					'deal'	: deal
					}
			
			api_utils.send_response(self,response)
		
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
		
app = webapp2.WSGIApplication([('/api/upload/request', UploadRequestHandler),
								('/api/upload/post', UploadPostHandler)
								],debug=True)