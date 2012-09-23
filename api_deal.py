import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
import levr_utils
from google.appengine.ext import db
from google.appengine.api import mail

'''
DEAL OBJECT :{
			#PUBLIC
			dealID:
			business:{
					businessID:
					businessName:
					vicinity:
					geoPoint:
					geoHash:
					}
			dealText:
			description:
			shareURL: URL
			geoPoint:
			geoHash:
			status:
			largeImg: URL
			smallImg: URL
			dateUploaded:
			dateEnd:
			isExclusive: bool
			barcode: None if empty
			redemptions: number
			tags: [list]
			#PRIVATE
			
			}
USER OBJECT :{
			#PUBLIC
			uid:
			alias:
			}
'''

class RedeemHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		inputs: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		#RESTRICTED
		try:
#			#spoof development vals
#			dealID	= 'ahNkZXZ-bGV2ci1wcm9kdWN0aW9uch8LEg1CdXNpbmVzc093bmVyGMIBDAsSBERlYWwYxAEM'
#			uid		= 'ahNkZXZ-bGV2ci1wcm9kdWN0aW9ucg8LEghDdXN0b21lchjMAQw'
			
			logging.info(dealID)
			logging.info(self.request.get('uid'))
#			
			if not api_utils.check_param(self,dealID,'dealID',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			user = levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			owner = dealID.parent()
			logging.debug(owner)
			
			#create and store notification entity
			note = levr.Notification(
									parent = owner,
									notification_type = 'redemption',
									user = uid,
									deal = dealID
									)
			note.put()
			logging.debug(levr_utils.log_model_props(note))
			
			#respond
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')

class AddFavoriteHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		#RESTRICTED
		try:
			
			logging.info(dealID)
			logging.info(self.request.get('uid'))
#			
			if not api_utils.check_param(self,dealID,'dealID',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			user = levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			#append dealID to favorites property
			user.favorites.append(dealID)
			logging.debug(user.favorites)
			
			#close entity
			user.put()
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
	
class DeleteFavoriteHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			logging.info(dealID)
			logging.info(self.request.get('uid'))
#			
			if not api_utils.check_param(self,dealID,'dealID',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			user = levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			#grab favorites list
			favorites	= user.favorites
			logging.debug(favorites)
			
			#generate new favorites list without requested dealID
			new_favorites	= [deal for deal in favorites if deal != dealID]
			logging.debug(new_favorites)
			
			#reassign user favorites to new list
			user.favorites	= new_favorites
			logging.debug(user.favorites)
			
			#close entity
			user.put()
			
			api_utils.send_response(self,{},user
								)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		

class ReportHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			logging.info(dealID)
			logging.info(self.request.get('uid'))
#			
			if not api_utils.check_param(self,dealID,'dealID',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			user = levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
#			
#			logging.warning(dealID)
#			#get human readable info for email
#			deal = levr.Deal.get(dealID)
#			if not deal:
#				api_utils.send_error('Invalid parameter: dealID')
#			business_name = deal.business_name
#			
#			user = levr.Customer.get(uid)
#			if not user:
#				api_utils.send_error('Invalid parameter: uid')
#			alias = user.alias
#			
			
			#create report Entity
			report = levr.ReportedDeal(
									uid = uid,
									dealID = dealID
									).put()
			
			
			#send notification via email
			message = mail.EmailMessage(
				sender	="LEVR AUTOMATED <patrick@levr.com>",
				subject	="New Reported Deal",
				to		="patrick@levr.com")
			
			logging.debug(message)
			body = 'New Reported Deal\n\n'
			message.body = body
			logging.debug(message.body)
			message.send()
			
			
			
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')

class DealImgHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: None
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		#get inputs
		'''Returns ONLY an image for a deal specified by dealID
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('img')
			if not api_utils.check_param(self,dealID,'dealID',True):
				return
			uid = self.request.get('size')
			if not api_utils.check_param(self,size,'size',True):
				return
			
			
			logging.debug(dealID)
			logging.debug(size)
			
			#get deal object
			deal = db.get(dealID)

			#get the blob
			blob_key = deal.img
			
			logging.debug(dir(blob_key.properties))
			#read the blob data into a string !!!! important !!!!
			blob_data = blob_key.open().read()
			
			#pass blob data to the image handler
			img			= images.Image(blob_data)
			#get img dimensions
			img_width	= img.width
			img_height	= img.height
			logging.debug(img_width)
			logging.debug(img_height)
			
			#define output parameters
			if size == 'dealDetail':
				#view for top of deal screen
				aspect_ratio 	= 3. 	#width/height
				output_width 	= 640.	#arbitrary standard
			elif size == 'list':
				#view for in deal or favorites list
				aspect_ratio	= 1.	#width/height
				output_width	= 200.	#arbitrary standard
			elif size == 'fullSize':
				#full size image
				aspect_ratio	= float(img_width)/float(img_height)
				output_width	= float(img_width)
	#			self.response.out.write(deal.img)
			elif size == 'webShare':
				aspect_ratio	= 4.
				output_width	= 600.
			elif size == 'facebook':
				aspect_ratio 	= 1.
				output_width	= 250.
			elif size == 'emptySet':
				aspect_ratio	= 3.
				output_width	= 640.
			elif size == 'widget':
				aspect_ratio	= 1.
				output_width	= 150.
			else:
				raise Exception('invalid size parameter')
				
				##set this to some default for production
			#calculate output_height from output_width
			output_height	= output_width/aspect_ratio
			
			##get crop dimensions
			if img_width > img_height*aspect_ratio:
				#width must be cropped
				w_crop_unscaled = (img_width-img_height*aspect_ratio)/2
				w_crop 	= float(w_crop_unscaled/img_width)
				left_x 	= w_crop
				right_x = 1.-w_crop
				top_y	= 0.
				bot_y	= 1.
			else:
				#height must be cropped
				h_crop_unscaled = (img_height-img_width/aspect_ratio)/2
				h_crop	= float(h_crop_unscaled/img_height)
				left_x	= 0.
				right_x	= 1.
				top_y	= h_crop
				bot_y	= 1.-h_crop
		
			#crop image to aspect ratio
			img.crop(left_x,top_y,right_x,bot_y)
			logging.debug(img)
			
			#resize cropped image
			img.resize(width=int(output_width),height=int(output_height))
			logging.debug(img)
			output_img = img.execute_transforms(output_encoding=images.JPEG)
#			logging.debug(output_img)
		except:
			levr.log_error(self.request)
			output_img = None
		finally:
			try:
				self.response.headers['Content-Type'] = 'image/jpeg'
				self.response.out.write(output_img)
			except:
				levr.log_error()
		

class DealInfoHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Get information about a deal.
		
		Input: None
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				<DEAL OBJECT>
				}
			}
		'''
		try:
			logging.info(dealID)
#			
			if not api_utils.check_param(self,dealID,'dealID',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
			logging.warning(type(dealID))
			deal = levr.Deal.get(dealID)
			if not deal:
				api_utils.send_error(self,'Invalid dealID: '+str(dealID))
			
			response = api_utils.package_deal(deal)
			
			api_utils.send_response(self,response)
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')

app = webapp2.WSGIApplication([('/api/deal/(.*)/redeem.*', RedeemHandler),
								('/api/deal/(.*)/addfavorite.*', AddFavoriteHandler),
								('/api/deal/(.*)/deletefavorite.*', DeleteFavoriteHandler),
								('/api/deal/(.*)/report.*', ReportHandler),
								('/api/deal/(.*)/img.*', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)
								],debug=True)