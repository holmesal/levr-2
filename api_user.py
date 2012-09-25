import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
from datetime import datetime
from google.appengine.ext import db
#from google.appengine.api import mail

class UserFavoritesHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		Get all of a users favorite deals
		
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
			logging.info("\n\nGET USER FAVORITES")
			
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
			
			
			#GET ENTITIES
			user = db.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			#grab all favorites
			favorites = user.favorites
			
			#check list is longer than offset
			if favorites.__len__() > offset:
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
			else:
				#favorites is either empty or the offset is past the length of it
				deals = []
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
		Get all of a users uploaded deals
		
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
			logging.info("\n\nGET USER UPLOADS")
			
			LIMIT_DEFAULT = 10
			OFFSET_DEFAULT = 0
			
			
			#CHECK PARAMS
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
			
			#GET ENTITIES
			user = db.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			
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
		
class UserGetFollowersHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		Get all of a users followers
		
		#RESTRICTED
		inputs: limit, offset
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				followers:[
					<USER OBJECT>
					]
				}
		'''
		try:
			logging.info('GET USER FOLLOWERS')
			logging.info(uid)
			
			LIMIT_DEFAULT = 20
			OFFSET_DEFAULT = 0
			#CHECK PARAMS
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
			
			#GET ENTITIES
			user = db.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			
			
			#PERFORM ACTIONS
			
			#package each follower into <USER OBJECT>
			followers = [api_utils.package_user(u) for u in levr.Customer.get(user.followers)]
			
			response = {
					'numResults'	: followers.__len__(),
					'followers'		: followers
					}
			#respond
			api_utils.send_response(self,response,user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
class UserAddFollowHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		A user (specified in ?uid=USER_ID) follows the user specified in (/api/USER_ID/follow)
		
		inputs: uid(required)
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			logging.info('\n\nUSER ADD FOLLOWER')
			
			#CHECK PARAMS
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
				
			actorID = self.request.get('uid')
			if not api_utils.check_param(self,actorID,'uid','key',True):
				return
			else:
				actorID = db.Key(enc.decrypt_key(actorID))
			
			
			#GET ENTITIES
			[user,actor] = db.get([uid,actorID])
			if not user or user.kind() != 'Customer':
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			if not actor or actor.kind() != 'Customer':
				api_utils.send_error(self,'Invalid follower uid: '+str(actorID))
				return
			
			
			#PERFORM ACTIONS
			if not levr.create_notification('newFollower',uid,actorID):
				api_utils.send_error(self,'Server Error')
				return
			
			#get notifications
			
			
			#respond
			api_utils.send_response(self,{},actor)
			
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
class UserUnfollowHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''
		A user (specified in ?uid=USER_ID) stops following the user specified in (/api/USER_ID/follow)
		If the user is not a follower and they request to unfollow, then nothing happens and success is true
		
		inputs: followerID(required)
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			logging.info('\n\nUSER REMOVE FOLLOWER')
			
			#CHECK PARAMS
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
				
			actorID = self.request.get('uid')
			if not api_utils.check_param(self,actorID,'uid','key',True):
				return
			else:
				actorID = db.Key(enc.decrypt_key(actorID))
			
			
			#GET ENTITIES
			[user,actor] = db.get([uid,actorID])
			if not user or user.kind() != 'Customer':
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			if not actor or actor.kind() != 'Customer':
				api_utils.send_error(self,'Invalid follower uid: '+str(actorID))
				return
			
			
			#PERFORM ACTIONS
			#grab a list of existing followers
			old_followers = user.followers
			logging.debug(old_followers)
			
			#check if in list of existing followers
			if actorID in old_followers:
				logging.debug('Follower exists')
				#create new list of followers that excludes the requested id
				new_followers = [u for u in old_followers if u != actorID]
				logging.debug(new_followers)
				
				#replace list of followers
				user.followers = new_followers
				
				#replace user that lost a follower
				db.put(user)
			else:
				logging.debug('follower does not exist. Do nothing')
			
			#respond
			api_utils.send_response(self,{},actor)
			
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
class UserImgHandler(webapp2.RequestHandler):
	def get(self,uid):
		'''Returns ONLY an image for a deal specified by dealID
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('\n\n\nIMAGE')
			
			
			#CHECK PARAMS
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
				logging.debug(uid)
			
			size = self.request.get('size')
			if not api_utils.check_param(self,size,'size','str',True):
				return
			
			#GET ENTITIES
			user = db.get(dealID)
			if not user or user.kind() != 'Customer':
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			#get the blob
			blob_key = user.img
			
			#send image to response output
			if not api_utils.send_img(self,blob_key,size):
				return
			
		except:
			levr.log_error()
			self.response.headers['Content-Type'] = 'image/jpeg'
			self.response.out.write(None)


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
		inputs: sinceDate(required)
		
		Output:{
			meta:{
				success :<bool>
				errorMsg : <str>
				}
			response:{
					numResults : <int>
					notifications:[
						<NOTIFICATION OBJECT>
						]
				}
		'''
		try:

			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
				
			#sinceDate is the date of how far back you want notifications
			sinceDate = self.request.get('sinceDate')
			if not api_utils.check_param(self,sinceDate,'sinceDate','int',False):
				sinceDate = None
			
			
			logging.debug('sinceDate: '+str(sinceDate))
			user = levr.Customer.get(uid)
			logging.debug(levr.log_model_props(user))
			logging.debug('last notified: '+str(user.last_notified))
			
			#get notifications 
			notifications = user.get_notifications(sinceDate)
			logging.debug('notifications: '+str(notifications.__len__()))
			
			packaged_notifications = [api_utils.package_notification(n) for n in notifications]
			
			
			response = {
					'numResults'	: packaged_notifications.__len__(),
					'notifications'	: packaged_notifications
					}
			
			api_utils.send_response(self,response)
#			logging.debug(notes)
			
			#replace user
			#!!!!!!!IMPORTANT!!!!
			user.put()
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
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
				
			#get user entity
			user = levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			
			#create response object
			response = {
					'user'	: api_utils.package_user(user)
					}
			
			#respond
			api_utils.send_response(self,response,user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		
		
app = webapp2.WSGIApplication([('/api/user/(.*)/favorites', UserFavoritesHandler),
								('/api/user/(.*)/uploads', UserUploadsHandler),
								('/api/user/(.*)/followers', UserGetFollowersHandler),
								('/api/user/(.*)/follow', UserAddFollowHandler),
								('/api/user/(.*)/unfollow', UserUnfollowHandler),
								('/api/user/(.*)/img', UserImgHandler),
								('/api/user/(.*)/cashout', UserCashOutHandler),
								('/api/user/(.*)/notifications', UserNotificationsHandler),
								('/api/user/(.*)', UserInfoHandler)],debug=True)