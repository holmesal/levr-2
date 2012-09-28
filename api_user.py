import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
from datetime import datetime
from google.appengine.ext import db
#from google.appengine.api import mail

def authorize(handler_method):
	'''
	Decorator checks the privacy level of the request.
	If the uid is valid and the user exists, it checks the levr_token to  privacy level
	
	'''
	def check(self,*args,**kwargs):
		try:
			logging.debug('PUBLIC OR PRIVATE DECORATOR\n\n\n')
#			logging.debug(levr.log_dir(self.request))
			logging.debug(args)
			logging.debug(kwargs)
			
			#CHECK USER
			uid = args[0]
			if not api_utils.check_param(self,uid,'uid','key',True):
				raise Exception('uid: '+str(uid))
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			
			#GET ENTITIES
			user = db.get(uid)
			if not user or user.kind() != 'Customer':
				raise Exception('uid: '+str(uid))
			
			levr_token = self.request.get('levr_token')
			
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
def private(handler_method):
	'''
	Decorator used to reject calls that require private auth and do not have them
	'''
	def check(self,*args,**kwargs):
		try:
			logging.debug('PRIVATE SCREENING DECORATOR\n\n\n')
			logging.debug(args)
			logging.debug(kwargs)
			
			private = kwargs.get('private')
			
			if private:
				#RPC is authorized
				handler_method(self,*args,**kwargs)
			else:
				#call is unauthorized - reject
				api_utils.send_error(self,'Not Authorized')
			
			
			
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
	
	return check
	
class UserFavoritesHandler(webapp2.RequestHandler):
	@authorize
	@private
	def get(self,*args,**kwargs):
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
			logging.info(kwargs)
			logging.info(args)
			
			LIMIT_DEFAULT = 20
			OFFSET_DEFAULT = 0
			
			user = kwargs.get('user')
			uid = user.key()
			private = kwargs.get('private')
			limit = self.request.get('limit')
			if not api_utils.check_param(self,limit,'limit','int',False):
				#limit not passed
				limit = LIMIT_DEFAULT
				
			offset = self.request.get('offset')
			if not api_utils.check_param(self,offset,'offset','int',False):
				#limit not passed
				offset = OFFSET_DEFAULT
			
			
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
	@authorize
	def get(self,*args,**kwargs):
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
			
			user = kwargs.get('user')
			private = kwargs.get('private')
			
			
			LIMIT_DEFAULT = 10
			OFFSET_DEFAULT = 0
			
			
			limit = self.request.get('limit')
			if not api_utils.check_param(self,limit,'limit','int',False):
				#limit not passed
				limit = LIMIT_DEFAULT
				
			offset = self.request.get('offset')
			if not api_utils.check_param(self,offset,'offset','int',False):
				#limit not passed
				offset = OFFSET_DEFAULT
			
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
	@authorize
	def get(self,*args,**kwargs):
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
			logging.info('GET USER FOLLOWERS\n\n\n')
			
			user = kwargs.get('user')
			uid = user.key()
			private = kwargs.get('private')
			
			LIMIT_DEFAULT = 20
			OFFSET_DEFAULT = 0
			#CHECK PARAMS
			limit = self.request.get('limit')
			if not api_utils.check_param(self,limit,'limit','int',False):
				#limit not passed
				limit = LIMIT_DEFAULT
			
			offset = self.request.get('offset')
			if not api_utils.check_param(self,offset,'offset','int',False):
				#limit not passed
				offset = OFFSET_DEFAULT
			
			
			
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
	@authorize
	def get(self,*args,**kwargs):
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
			logging.info('USER ADD FOLLOWER\n\n\n')
			user = kwargs.get('user')
			uid = user.key()
			private = kwargs.get('private')
			
			
			actorID = self.request.get('uid')
			if not api_utils.check_param(self,actorID,'uid','key',True):
				return
			else:
				actorID = db.Key(enc.decrypt_key(actorID))
			
			
			#GET ENTITIES
			actor = db.get(actorID)
			if not actor or actor.kind() != 'Customer':
				api_utils.send_error(self,'Invalid follower uid: '+str(actorID))
				return
			
			
			#PERFORM ACTIONS
			if not levr.create_notification('newFollower',user.key(),actorID):
				api_utils.send_error(self,'Server Error')
				return
			
			#get notifications
			
			
			#respond
			api_utils.send_response(self,{'dt':str(actor.date_last_notified)},actor)
			
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
class UserUnfollowHandler(webapp2.RequestHandler):
	@authorize
	def get(self,*args,**kwargs):
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
			user = kwargs.get('user')
			uid = user.key()
			private = kwargs.get('private')
			
			#CHECK PARAMS
			actorID = self.request.get('uid')
			if not api_utils.check_param(self,actorID,'uid','key',True):
				return
			else:
				actorID = db.Key(enc.decrypt_key(actorID))
			
			#GET ENTITIES
			actor = db.get(actorID)
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
	@authorize
	def get(self,*args,**kwargs):
		'''Returns ONLY an image for a deal specified by uid
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('IMAGE\n\n\n')
			user = kwargs.get('user')
			uid = user.key()
			private = kwargs.get('private')
			
			
			size = self.request.get('size')
			if not api_utils.check_param(self,size,'size','str',True):
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
	@authorize
	def get(self,*args,**kwargs):
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
	@authorize
	@private
	def get(self,*args,**kwargs):
		'''
		#RESTRICTED
		inputs: since(required)
		
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
			user = kwargs.get('user')
			uid = user.key()
			private = kwargs.get('private')
			
			
			#sinceDate is the date of how far back you want notifications
			sinceDate = kwargs.get('since')
			if not api_utils.check_param(self,sinceDate,'sinceDate','int',False):
				sinceDate = None
			
			
			logging.debug('sinceDate: '+str(sinceDate))
			logging.debug('last notified: '+str(user.last_notified))
			
			#get notifications 
			notifications = user.get_notifications(sinceDate)
			logging.debug('notifications: '+str(notifications.__len__()))
			
			#package up the notifications
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
	@authorize
	def get(self,*args,**kwargs):
		'''
		#PARTIALLY RESTRICTED
		inputs:
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
			user 	= kwargs.get('user')
			private	= kwargs.get('private')
			#create response object
			response = {
					'user'	: api_utils.package_user(user,private)
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