import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
#from api_utils import private
import levr_utils
from google.appengine.ext import db
from google.appengine.api import mail


#class RedeemHandler(webapp2.RequestHandler):
#	@api_utils.validate('deal','param',user=True)
#	@api_utils.private
#	def get(self,*args,**kwargs):
#		'''
#		inputs: uid
#		Response: none
#		'''
#		#RESTRICTED
#		try:
#			user 	= kwargs.get('actor')
#			deal 	= kwargs.get('deal')
#			
#			uid 	= user.key()
#			dealID 	= deal.key()
#			
#			
#			#PERFORM ACTIONS
#			owner = dealID.parent()
#			logging.debug(owner)
#			
#			if not levr.create_notification('redemption',dealID.parent(),uid,dealID):
#				raise Exception('Problem in create_notifications')
#			
#			deal.count_redeemed += 1
#			
#			#respond
#			api_utils.send_response(self,{},user)
#		except:
#			levr.log_error(self.request)
#			api_utils.send_error(self,'Server Error')
#

#class AddFavoriteHandler(webapp2.RequestHandler):
#	@api_utils.validate('deal','param',user=True)
#	@api_utils.private
#	def get(self,*args,**kwargs):
#		'''
#		Input: uid
#		Response: None
#		'''
#		#RESTRICTED
#		try:
#			user 	= kwargs.get('actor')
#			deal 	= kwargs.get('deal')
#			
#			uid 	= user.key()
#			dealID 	= deal.key()
#			
#			
#			#PERFORM ACTIONS
#			logging.debug(levr.log_model_props(user))
#			#only add to favorites if not already in favorites
#			if dealID not in user.favorites:
#				logging.debug('Flag not in favorites')
#				#append dealID to favorites property
#				user.favorites.append(dealID)
#				logging.debug(user.favorites)
#				
#				#create favorite notification
#				levr.create_notification('favorite',dealID.parent(),uid,dealID)
#			
#				#close entity
#				user.put()
#			else:
#				logging.debug('Already upvoted!')
#			
#			api_utils.send_response(self,{},user)
#		except:
#			levr.log_error(self.request)
#			api_utils.send_error(self,'Server Error')
#			

class UpvoteHandler(webapp2.RequestHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,dealID,*args,**kwargs):
		try:
			logging.debug('UPVOTE\n\n\n')
			logging.debug(kwargs)
			
			
			user 	= kwargs.get('actor')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			
			#favorite
			logging.debug(levr.log_model_props(user,['upvotes','downvotes','favorites']))
			logging.debug(levr.log_model_props(deal,['upvotes','downvotes']))
				
				
				
			if dealID in user.upvotes:
				logging.debug('flag deal in upvotes')
				#user is removing the upvote
				#remove the offending deal from the user upvotes
				user.upvotes.remove(dealID)
				
				#decrement the deal upvotes
				deal.upvotes -= 1
				#do not change the karma of the user who uploaded it
				#do not remove from favorites
				#do not remove notification
				
				db.put([user,deal])
				
			elif dealID in user.downvotes:
				logging.debug('flag deal is in downvotes')
				#remove deal from downvotes
				user.downvotes.remove(dealID)
				#decrement the deals downvotes
				deal.downvotes -= 1
				
				#add deal to upvotes
 				user.upvotes.append(dealID)
				#increment the number of upvotes
				deal.upvotes += 1
				#add deal to favorites
				if dealID not in user.favorites:
 					user.favorites.append(dealID)
					pass
				
				#do not change the karma of the user who uploaded
				#do not add notification for the ninja
				db.put([user,deal])
			else:
				logging.debug('flag deal not in upvotes or downvotes')
				
				#get owner of the deal
				ninja = levr.Customer.get(deal.key().parent())
				#compare owner to user doing the voting
				if ninja.key() == user.key():
					#ninja is upvoting his own deal
					#increase that users karma! reward for uploading a deal!
					user.karma += 1
					#level check!
					api_utils.level_check(user)
				else:
					#increase the ninjas karma
					ninja.karma += 1
					#level check!
					api_utils.level_check(ninja)
					#replace ninja. we dont want him anymore
					ninja.put()
				
				
				#add to upvote list
 				user.upvotes.append(dealID)
				
#				#increase the deal upvotes
				deal.upvotes += 1
				
				
				
				
				#add to users favorites list if not there already
				if dealID not in user.favorites:
					user.favorites.append(dealID)
					#create favorite notification for the ninja that uploaded
					levr.create_notification('favorite',ninja.key(),uid,dealID)
				
				
				db.put([user,deal])
				#put actor and ninja and deal back
			
			
			response = {
					'deal':api_utils.package_deal(deal)
					}
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')

class DownvoteHandler(webapp2.RequestHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,dealID,*args,**kwargs):
		try:
			logging.debug('DOWNVOTE\n\n\n')
			logging.debug(kwargs)
			
			
			user 	= kwargs.get('actor')
			uid 	= user.key()
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			
			
			#favorite
			logging.debug(levr.log_model_props(user))
			
			if dealID in user.downvotes:
				logging.debug('flag deal is in downvotes')
				
				user.downvotes.remove(dealID)
				
				#decrement the deal downvotes
				deal.downvotes -= 1
				#do not change the karma of the user who uploaded it
				#do not add to favorites
				#do not create notification
				
				db.put([user,deal])
				
			
			elif dealID in user.upvotes:
				logging.debug('flag deal is in downvotes')
				
				#remove from user upvotes
				user.upvotes.remove(dealID)
				#decrement deal upvotes
				deal.upvotes -= 1
				
				#add to user downvotes
				user.downvotes.append(dealID)
				#increment deal downvotes
				deal.downvotes += 1
				
				#replace entities
				db.put([user,deal])
				
			else:
				logging.debug('Flag deal not in upvotes or downvotes')
				
				#add to user downvotes
				user.downvotes.append(dealID)
				
				#downvote deal
				deal.downvotes += 1
				
				#replace entities
				db.put([user,deal])
				
				
			
			
			response = {
					'deal':api_utils.package_deal(deal)
					}
			api_utils.send_response(self,response,user)
			
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')



class DeleteFavoriteHandler(webapp2.RequestHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		Input: uid
		response: {}
		'''
		try:
			logging.debug('DELETE FAVORITE\n\n\n')
			logging.debug(kwargs)
			
			user 	= kwargs.get('actor')
			deal 	= kwargs.get('deal')
			
			uid 	= user.key()
			dealID 	= deal.key()
			
			
			#if the deal is in the users favorites, remove it. else do nothing
			if dealID in user.favorites:
				user.favorites.remove(dealID)
			
			#replace entities
			db.put(user)
			
			
			response = {}
			
			api_utils.send_response(self,reponse,user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')
		
		

class ReportHandler(webapp2.RequestHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
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
			logging.debug("REPORT\n\n\n")
			logging.debug(kwargs)
			
			
			user	= kwargs.get('actor')
			deal	= kwargs.get('deal')
			
			uid		= user.key()
			dealID	= deal.key()
			
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
			body += str(user.email) +' is reporting '+str(deal.deal_text)
			message.body = body
			logging.debug(message.body)
			message.send()
			
			
			
			api_utils.send_response(self,{},user)
		except:
			levr.log_error(self.request)
			api_utils.send_error(self,'Server Error')

class DealImgHandler(webapp2.RequestHandler):
	@api_utils.validate('deal',None,size=True)
	def get(self,*args,**kwargs):
		'''Returns ONLY an image for a deal specified by dealID
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('IMAGE\n\n\n')
			logging.debug(kwargs)
			
			deal	= kwargs.get('deal')
			size	= kwargs.get('size')
			private	= kwargs.get('private')
			
			
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
	@api_utils.validate('deal',None)
	def get(self,*args,**kwargs):
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
			logging.debug('DEAL INFO\n\n\n')
			logging.debug(kwargs)
			deal	= kwargs.get('deal')
			private	= kwargs.get('private')
			
			response = {
				'deal'	: api_utils.package_deal(deal)
			}
			api_utils.send_response(self,response)
		except:
			levr.log_error(self.request.body)
			api_utils.send_error(self,'Server Error')

app = webapp2.WSGIApplication([ #('/api/deal/(.*)/redeem.*', RedeemHandler),
								#('/api/deal/(.*)/favorite.*', AddFavoriteHandler),
								('/api/deal/(.*)/upvote', UpvoteHandler),
								('/api/deal/(.*)/downvote', DownvoteHandler),
								('/api/deal/(.*)/deleteFavorite.*', DeleteFavoriteHandler),
								('/api/deal/(.*)/report.*', ReportHandler),
								('/api/deal/(.*)/img.*', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)
								],debug=True)