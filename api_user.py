from api_utils import private
from google.appengine.ext import db
import api_utils
import levr_classes as levr
import logging
import webapp2
#import levr_encrypt as enc
#from datetime import datetime
#from google.appengine.api import mail


class UserFavoritesHandler(webapp2.RequestHandler):
	@api_utils.validate('user','url',limit=False,offset=False,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		/user/uid/favorites
		
		Get all of a users favorite deals
		
		inputs: 
		
		response:{
			numResults: <int>
			deals: [<deal>,<deal>]
			}
		'''
		#RESTRICTED
		try:
			logging.info("\n\nGET USER FAVORITES")
			logging.info(kwargs)
			logging.info(args)
			
			user 	= kwargs.get('user')
#			uid 	= user.key()
			private = kwargs.get('private')
			limit 	= kwargs.get('limit')
			offset 	= kwargs.get('offset')
			
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
				
				deals = []
				
				#package each deal object
				for deal in favorites:
					if deal:
						deals.append(api_utils.package_deal(deal,False))
			else:
				#favorites is either empty or the offset is past the length of it
				deals = []
			#create response object
			response = {
					'numResults': str(favorites.__len__()),
					'deals'		: deals
					}
			logging.debug(response)
			#respond
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		

class UserUploadsHandler(webapp2.RequestHandler):
	@api_utils.validate('user','url',limit=False,offset=False,levrToken=False)
	def get(self,*args,**kwargs):
		'''
		Get all of a users uploaded deals
		
		inputs: limit(optional), offset(optional)
		response:{
			deal: <DEAL OBJECT>
			}
		'''
		try:
			logging.info("\n\nGET USER UPLOADS")
			logging.debug(kwargs)
			user 	= kwargs.get('user')
			uid 	= user.key()
			private = kwargs.get('private')
			limit 	= kwargs.get('limit')
			offset 	= kwargs.get('offset')
			
			#grab all deals that are owned by the specified customer
			deals = levr.Deal.all().ancestor(uid).fetch(limit,offset=offset)
			
			#package up the dealios
			packaged_deals = [api_utils.package_deal(deal,private) for deal in deals]
			
			#package the user object
			packaged_user = api_utils.package_user(user,private)
			
			#create response object
			response = {
					'numResults': str(packaged_deals.__len__()),
					'deals'		: packaged_deals,
					'user'		: packaged_user
					}
			
			#respond
			api_utils.send_response(self,response,user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class UserGetFollowersHandler(webapp2.RequestHandler):
	@api_utils.validate('user','url',limit=False,offset=False,levrToken=False)
	def get(self,*args,**kwargs):
		'''
		Get all of a users followers
		
		#RESTRICTED
		inputs:
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
			logging.debug(kwargs)
			user 	= kwargs.get('user')
#			uid 	= user.key()
			private = kwargs.get('private')
#			limit 	= kwargs.get('limit')
#			offset 	= kwargs.get('offset')
			
			
			
			#PERFORM ACTIONS
			
			#package each follower into <USER OBJECT>
			followers = [api_utils.package_user(u) for u in levr.Customer.get(user.followers)]
			logging.debug(followers)
			
			response = {
					'numResults'	: followers.__len__(),
					'followers'		: followers
					}
			#respond
			api_utils.send_response(self,response,user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class UserAddFollowHandler(api_utils.BaseClass):
	@api_utils.validate('user','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		A user (specified in ?uid=USER_ID) follows the user specified in (/api/USER_ID/follow)
		
		inputs: uid(required)
		
		Response:{
			None
			}
		'''
		try:
			logging.info('\n\n\n\t\t\t USER ADD FOLLOWER\n\n\n')
			user 	= kwargs.get('user')
			actor	= kwargs.get('actor')
			actorID = actor.key()
			private = kwargs.get('private')
			
			#add actor to the list of followers
			if actorID not in user.followers:
				user.followers.append(actorID)
			
			to_be_notified = user
			
			levr.Notification().new_follower(to_be_notified, actor)
			# TODO: test new notification
			
			#get notifications
			db.put([user,actor])
			
			response = {
					'dt':str(actor.date_last_notified)
					}
			self.send_response(response, actor)
			
		except:
			self.send_fail()

class UserUnfollowHandler(webapp2.RequestHandler):
	@api_utils.validate('user','param',user=True,levrToken=True)
	@api_utils.private
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
			logging.debug(kwargs)
			user = kwargs.get('user')
#			uid = user.key()
			actor = kwargs.get('actor')
			actorID = actor.key()
			private = kwargs.get('private')
			
			
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
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class UserImgHandler(webapp2.RequestHandler):
	@api_utils.validate('user',None,size=True)
	def get(self,*args,**kwargs):
		'''Returns ONLY an image for a deal specified by uid
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('IMAGE\n\n\n')
			user	= kwargs.get('user')
#			uid		= user.key()
			size	= kwargs.get('size')
			
			# fetch from relational db
			photo = user.img_ref.get()
			
			assert photo, 'Customer does not have an image in the database'
			# grab img key from blobstore
			blob_key = photo.img
			
			
			#send image to response output
			if not api_utils.send_img(self,blob_key,size):
				return
			
			#test
		except:
			levr.log_error()
			self.response.headers['Content-Type'] = 'image/jpeg'
			self.response.out.write(None)


class UserNotificationsHandler(api_utils.BaseClass):
	@api_utils.validate('user','url',limit=False,offset=False,since=False,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		# TODO: test this
		'''
		#RESTRICTED
		inputs: limit,offset,since
		response:{
				numResults : <int>
				notifications:[
					<NOTIFICATION OBJECT>
					]
			}
		'''
		try:
			logging.info('\n\n\nNOTIFICATIONS\n\n\n')
			
			user		= kwargs.get('user')
			private		= kwargs.get('private')
			sinceDate	= kwargs.get('since')

			logging.debug('sinceDate: '+str(sinceDate))
			logging.debug('last notified: '+str(user.last_notified))
			
			#get notifications 
			notifications = user.get_notifications(sinceDate)
			logging.debug('notifications: '+str(notifications.__len__()))
			
			#package up the notifications
			packaged_notifications = api_utils.package_notification_multi(notifications)
			
			response = {
					'numResults'	: packaged_notifications.__len__(),
					'notifications'	: packaged_notifications
					}
			
			self.send_response(response)
			
			#replace user
			#!!!!!!!IMPORTANT!!!!
			user.put()
		except:
			self.send_fail()
		
		
class UserInfoHandler(webapp2.RequestHandler):
	@api_utils.validate('user','url',levrToken=False)
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
			logging.debug('USER INFO\n\n')
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
								('/api/user/(.*)/notifications', UserNotificationsHandler),
								('/api/user/(.*)', UserInfoHandler)
								],debug=True)