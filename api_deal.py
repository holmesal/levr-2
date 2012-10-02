import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
#from api_utils import private
import levr_utils
from google.appengine.ext import db
from google.appengine.api import mail

def authorize(handler_method):
	'''
	Decorator checks the privacy level of the request.
	If the user is identified as the owner of the deal, then private
	
	'''
	def check(self,*args,**kwargs):
		try:
			logging.debug('AUTHORIZE DECORATOR\n\n\n')
#			logging.debug(levr.log_dir(self.request))
			logging.debug(args)
			logging.debug(kwargs)
			logging.debug(handler_method)
			
			dealID = args[0]
			#CHECK PARAMS
			if not api_utils.check_param(self,dealID,'dealID','key',True):
				raise Exception('dealID: '+str(dealID))
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
			
			#CHECK USER
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid','key',True):
				raise Exception('uid: '+str(uid))
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			#GET ENTITIES
			[deal,user] = db.get([dealID,uid])
			if not deal or deal.kind() != 'Deal':
				raise Exception('dealID: '+str(dealID))
			if not user or user.kind() != 'Customer':
				raise Exception('uid: '+str(uid))
			
			levr_token = self.request.get('levrToken')
			
			#if the levr_token matches up, then private request, otherwise public
			if user.levr_token == levr_token:
				private = True
			else:
				private = False
			
			logging.debug(private)
			
			
			#sends user object, deal object, and private=True/False
			kwargs.update({
						'user'	: user,
						'deal'	: deal,
						'private': private
						})
		except Exception,e:
			api_utils.send_error(self,'Invalid parameter, '+str(e))
		else:
			handler_method(self,*args,**kwargs)
	
	return check



		
		

class RedeemHandler(webapp2.RequestHandler):
	@authorize
	@api_utils.private
	def get(self,*args,**kwargs):
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
			user 	= kwargs.get('user')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			
			#PERFORM ACTIONS
			owner = dealID.parent()
			logging.debug(owner)
			
			if not levr.create_notification('redemption',dealID.parent(),uid,dealID):
				raise Exception('Problem in create_notifications')
			
			deal.count_redeemed += 1
			
			#respond
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')

class AddFavoriteHandler(webapp2.RequestHandler):
	@authorize
	@api_utils.private
	def get(self,*args,**kwargs):
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
			user 	= kwargs.get('user')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			
			#PERFORM ACTIONS
			logging.debug(levr.log_model_props(user))
			#only add to favorites if not already in favorites
			if dealID not in user.favorites:
				logging.debug('Flag not in favorites')
				#append dealID to favorites property
				user.favorites.append(dealID)
				logging.debug(user.favorites)
				
				#create favorite notification
				levr.create_notification('favorite',dealID.parent(),uid,dealID)
			
				#close entity
				user.put()
			else:
				logging.debug('Already upvoted!')
			
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
			
class UpvoteHandler(webapp2.RequestHandler):
	@authorize
	@api_utils.private
	def get(self,dealID,*args,**kwargs):
		try:

			user 	= kwargs.get('user')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			#GET ENTITIES
			deal = db.get(dealID)
			if not deal or deal.kind() != 'Deal':
				api_utils.send_error(self,'Invalid dealID: '+dealID)
				return
			
			
			
			#favorite
			logging.debug(levr.log_model_props(user))
			#only add to favorites if not already in favorites
			if dealID not in user.favorites:
				logging.debug('Flag not yet upvoted')
				#append dealID to favorites property
				user.favorites.append(dealID)
				logging.debug(user.favorites)
				
				#create favorite notification
				levr.create_notification('favorite',dealID.parent(),uid,dealID)
				
				#put user
				user.put()
				
				#increment
				deal.upvotes += 1
				
				#go increment that user's upvotes
				ninja = levr.Deal.get(deal.key().parent())
				ninja.karma += 1
				#level check!
				ninja = api_utils.level_check(ninja)
				#put that ninja back!
				ninja.put
			else:
				logging.debug('Flag already upvoted')
			
			#store
			deal.put()
			
			response = {'deal':api_utils.package_deal(deal)}
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')

class DownvoteHandler(webapp2.RequestHandler):
	@authorize
	@api_utils.private
	def get(self,dealID,*args,**kwargs):
		try:

			user 	= kwargs.get('user')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			#GET ENTITIES
			deal = db.get(dealID)
			if not deal or deal.kind() != 'Deal':
				api_utils.send_error(self,'Invalid dealID: '+dealID)
				return
			
			
			
			#favorite
			logging.debug(levr.log_model_props(user))
			
			#only do things if they haven't yet downvoted this deal
			if dealID not in user.downvotes:
				logging.debug('Flag not yet downvoted')
				#downvote
				deal.downvotes += 1
				
				#if in their favorites, remove
				if dealID in user.favorites:
					#generate new favorites list without requested dealID
					new_favorites	= [fav for fav in user.favorites if fav != dealID]
					logging.debug(new_favorites)
					
					#reassign user favorites to new list
					user.favorites	= new_favorites
				
				#add to downvotes
				user.downvotes.append(dealID)
				logging.debug(user.downvotes)
				
				#put user
				user.put()		
					
			else:
				logging.debug('Flag already downvoted')
			
			#store
			deal.put()
			
			response = {'deal':api_utils.package_deal(deal)}
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')


class DeleteFavoriteHandler(webapp2.RequestHandler):
	@authorize
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			user 	= kwargs.get('user')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			
			#PERFORM ACTIONS
			#grab favorites list
			favorites	= user.favorites
			logging.debug(favorites)
			
			#only go through the motions if the dealID is in the favorites list
			if dealID in user.favorites:
				#generate new favorites list without requested dealID
				new_favorites	= [deal for deal in favorites if deal != dealID]
				logging.debug(new_favorites)
				
				#reassign user favorites to new list
				user.favorites	= new_favorites
				logging.debug(user.favorites)
				
				#close entity
				user.put()
			
			
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		

class ReportHandler(webapp2.RequestHandler):
	@authorize
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		try:
			#CHECK PARAMS
			if not api_utils.check_param(self,dealID,'dealID','key',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
				
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid','key',True):
				return
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			
			#GET ENTITIES
			[user,deal] = db.get([uid,dealID])
			if not user or user.kind() != 'Customer':
				api_utils.send_error(self,'Invalid uid: '+uid)
				return
			if not deal or deal.kind() != 'Deal':
				api_utils.send_error(self,'Invalid dealID: '+str(dealID))
				return
			
			
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
		'''Returns ONLY an image for a deal specified by dealID
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('\n\n\nIMAGE')
			
			
			#CHECK PARAMS
			if not api_utils.check_param(self,dealID,'dealID','key',True):
				api_utils.send_error(self,'Invalid parameter, dealID: '+str(dealID))
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
			
			size = self.request.get('size')
			if not api_utils.check_param(self,size,'size','str',True):
				api_utils.send_error(self,'Invalid parameter, size: '+str(size))
				return
			
			#GET ENTITIES
			deal = db.get(dealID)
			if not deal or deal.kind() != 'Deal':
				api_utils.send_error(self,'Invalid parameter, dealID: '+str(dealID))
				return
			
			#get the blob
			blob_key = deal.img
			
			#send image to response output
			if not api_utils.send_img(self,blob_key,size):
				return
			
		except:
			levr.log_error()
			self.response.headers['Content-Type'] = 'image/jpeg'
			self.response.out.write(None)
			

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
			#CHECK PARAMS
			if not api_utils.check_param(self,dealID,'dealID','key',True):
				return
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
				logging.debug(dealID)
				
			
			
			#GET ENTITIES
			deal = db.get(dealID)
			if not deal or deal.kind() != 'Deal':
				api_utils.send_error(self,'Invalid dealID: '+dealID)
				return
			
			
			response = {
				'deal'	: api_utils.package_deal(deal)
			}
			api_utils.send_response(self,response)
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')

app = webapp2.WSGIApplication([('/api/deal/(.*)/redeem.*', RedeemHandler),
								#('/api/deal/(.*)/favorite.*', AddFavoriteHandler),
								('/api/deal/(.*)/upvote', UpvoteHandler),
								('/api/deal/(.*)/downvote', DownvoteHandler),
								#('/api/deal/(.*)/deleteFavorite.*', DeleteFavoriteHandler),
								('/api/deal/(.*)/report.*', ReportHandler),
								('/api/deal/(.*)/img.*', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)
								],debug=True)