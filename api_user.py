import webapp2
import logging


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
			logging.info(self.request.get('uid'))
			
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
				
			#grab list from offset to end
			#check list is longer than limit
			
			#grab list from beginning to limit or end
			
				#Hmmm What do we do here?
			
			
			
		except:
			levr.log_error(levr_utils.log_dir(self.request))
		

class UserUploadsHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		inputs: limit, offset
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
			pass
		except:
			levr.log_error(levr_utils.log_dir(self.request))
		
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
			pass
		except:
			levr.log_error(levr_utils.log_dir(self.request))
		
		
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
			levr.log_error(levr_utils.log_dir(self.request))
		
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
			levr.log_error(levr_utils.log_dir(self.request))
		
		
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
			levr.log_error(levr_utils.log_dir(self.request))
		
		
		
app = webapp2.WSGIApplication([('/api/user/(.*)/favorites', UserFavoritesHandler),
								('/api/user/(.*)/uploads', UserUploadsHandler),
								('/api/user/(.*)/friends', UserFriendsHandler),
								('/api/user/(.*)/img', UserImgHandler),
								('/api/user/(.*)/cashout', UserCashOutHandler),
								('/api/user/(.*)/notifications', UserNotificationsHandler),
								('/api/user/(.*)', UserInfoHandler)],debug=True)