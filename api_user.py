import webapp2
import logging


class UserFavoritesHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		inputs: limit, offset
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
			pass
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