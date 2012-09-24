import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
import levr_utils
from google.appengine.ext import db
#from google.appengine.api import mail

class UserFavoritesHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		inputs: limit(optional), offset(optional)
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				[string,string]
				}
		'''
		#RESTRICTED
		try:
			logging.info(uid)
			
			LIMIT_DEFAULT = 20
			OFFSET_DEFAULT = 0
			
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			limit = self.request.get('limit')
			if not api_utils.check_param(self,limit,'limit','int',False):
				#limit not passed
				limit = LIMIT_DEFAULT
				
			offset = self.request.get('offset')
			if not api_utils.check_param(self,offset,'offset','int',False):
				#limit not passed
				offset = OFFSET_DEFAULT
			
			#grab user entity
			user = levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			#grab all favorites
			favorites = user.favorites
			
			#check list is longer than offset
			if favorites.__len__() < offset:
				offset = 0
			#grab list from offset to end
			favorites = favorites[offset:]
			#check list is longer than limit
			if favorites.__len__() > limit:
				#there are more favorites than the limit requests so shorten favorites
				favorites = favorites[:limit]
			
			#fetch all favorite entities
			favorites = levr.Deal.get(favorites)
			
			#package each deal object
			deals = [api_utils.package_deal(deal,'public') for deal in favorites]
			
			#create response object
			response = {
					'numResults': str(favorites.__len__()),
					'deals'		: deals
					}
			
			#respond
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		

class UserUploadsHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		inputs: limit(optional), offset(optional)
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				deal: <DEAL OBJECT>
				}
		'''
		try:
			logging.info(uid)
			
			LIMIT_DEFAULT = 20
			OFFSET_DEFAULT = 0
			
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			limit = self.request.get('limit')
			if not api_utils.check_param(self,limit,'limit','int',False):
				#limit not passed
				limit = LIMIT_DEFAULT
				
			offset = self.request.get('offset')
			if not api_utils.check_param(self,offset,'offset','int',False):
				#limit not passed
				offset = OFFSET_DEFAULT
			
#			#grab user entity
#			user = levr.Customer.get(uid)
#			if not user:
#				api_utils.send_error(self,'Invalid uid: '+uid)
#				return
			
			#grab all deals that are owned by the specified customer
			deals = levr.Deal.all().ancestor(uid).fetch(limit,offset=offset)
			
			#package up the dealios
			packaged_deals = [api_utils.package_deal(deal,'public') for deal in deals]
			
			#create response object
			response = {
					'numResults': str(packaged_deals.__len__()),
					'deals'		: packaged_deals
					}
			
			#respond
			api_utils.send_response(self,response,user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
class UserFriendsHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		#RESTRICTED
		inputs: limit, offset
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				friends:[
					<USER OBJECT>
					]
				}
		'''
		try:
			logging.info(uid)
			
			LIMIT_DEFAULT = 20
			OFFSET_DEFAULT = 0
			
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			limit = self.request.get('limit')
			if not api_utils.check_param(self,limit,'limit','int',False):
				#limit not passed
				limit = LIMIT_DEFAULT
			
			offset = self.request.get('offset')
			if not api_utils.check_param(self,offset,'offset','int',False):
				#limit not passed
				offset = OFFSET_DEFAULT
			
			#grab user entity
			logging.warning('START USER')
			user = db.get(uid)
			logging.warning('END USER')
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			self.response.out.write('dooone')
			
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		
class UserImgHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		inputs: size
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			pass
		except:
			levr.log_error(levr_utils.log_dir(self.request))


class UserCashOutHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		#RESTRICTED
		inputs:
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			pass
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
class UserNotificationsHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		#RESTRICTED
		inputs: offset
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
					notifications:[
						<NOTIFICATION OBJECT>
						]
				}
		'''
		try:
			pass
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		
class UserInfoHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		#PARTIALLY RESTRICTED
		inputs: lat,lon,limit
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				<USER OBJECT>
				}
		'''
		try:
			pass
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		
		
app = webapp2.WSGIApplication([('/api/user/(.*)/favorites', UserFavoritesHandler),
								('/api/user/(.*)/uploads', UserUploadsHandler),
								('/api/user/(.*)/friends', UserFriendsHandler),
								('/api/user/(.*)/img', UserImgHandler),
								('/api/user/(.*)/cashout', UserCashOutHandler),
								('/api/user/(.*)/notifications', UserNotificationsHandler),
								('/api/user/(.*)', UserInfoHandler)],debug=True)