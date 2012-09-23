import webapp2
import logging


class UserFavoritesHandler(webapp2.RequestHandler):
	def get(self,uid):
		#RESTRICTED
		pass

class UserUploadsHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass
		
class UserFriendsHandler(webapp2.RequestHandler):
	def get(self,uid):
		#RESTRICTED
		pass
		
class UserImgHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass

class userImgHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass

class UserCashOutHandler(webapp2.RequestHandler):
	def get(self,uid):
		#RESTRICTED
		pass
		
class UserNotificationsHandler(webapp2.RequestHandler):
	def get(self,uid):
		#RESTRICTED
		pass
		
class UserInfoHandler(webapp2.RequestHandler):
	def get(self,uid):
		#PARTIALLY RESTRICTED
		pass
		
app = webapp2.WSGIApplication([('/api/user/(.*)/favorites', UserFavoritesHandler),
								('/api/user/(.*)/uploads', UserUploadsHandler),
								('/api/user/(.*)/friends', UserFriendsHandler),
								('/api/user/(.*)/img', UserImgHandler),
								('/api/user/(.*)/cashout', UserCashOutHandler),
								('/api/user/(.*)/notifications', UserNotificationsHandler),
								('/api/user/(.*)', UserInfoHandler)],debug=True)