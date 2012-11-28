import webapp2
import logging
import levr_classes as levr
import api_utils
import json
#from api_utils import private
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import taskqueue




class UpvoteHandler(api_utils.BaseHandler):
	@api_utils.validate('deal','param',
					user=True,
					levrToken=True,
					query=False
					)
	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		@todo: 
		'''
		try:
			logging.debug('UPVOTE\n\n\n')
			logging.debug(kwargs)
			
			
			user 	= kwargs.get('actor')
			deal 	= kwargs.get('deal')
			dealID 	= deal.key()
			query	= kwargs.get('query')
			
			if query:
				api_utils.KWLinker.register_like(deal, query)
			
			
			#===================================================================
			# Note, if this code changes, you should also change the code in /cronjobs/undeadActivity because it was copied and pasted...
			#===================================================================
			
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
				
				#do not change the karma of the user who uploaded
				#do not add notification for the ninja
				db.put([user,deal])
				pass
			else:
				logging.debug('flag deal not in upvotes or downvotes')
				
				# If the deal is in the users favorites, then they upvoted the deal at one point and then
				# removed that upvote either via another upvote or a downvote, and they are trying to upvote again
				# At this point, the deal should get its upvote back, but the ninja gets no karma because they do not
				# lose a karma point when the deal is downloaded
				if dealID not in user.favorites:
					#get owner of the deal
					ninja = levr.Customer.get(deal.key().parent())
					#check owner. if the owner is a dummy owner left over from an account transfer, grab the real owner.
					if ninja.email == 'dummy@levr.com':
						logging.debug('\n\n\n \t\t\t DUMMY NINJA! REDIRECTING REFERENCE TO THE REAL ONE!!! \n\n\n')
						ninja = levr.Customer.get(ninja.pw)
					
					#compare owner to user doing the voting
					if ninja.key() == user.key():
						#ninja is upvoting his own deal
						#increase that users karma! reward for uploading a deal!
						user.karma += 1
					else:
						#increase the ninjas karma
						ninja.karma += 1
						#replace ninja. we dont want him anymore
						ninja.put()
				
				
				#add to upvote list
				user.upvotes.append(dealID)
				
				#increase the deal upvotes
				deal.upvotes += 1
				
				
				
				
				#add to users favorites list if not there already
				if dealID not in user.favorites:
					user.favorites.append(dealID)
					#create favorite notification for the ninja that uploaded
					to_be_notified = ninja
					actor = user
					deal = deal
					levr.Notification().upvote(to_be_notified, actor, deal)
					# TEST: new notification
				
				db.put([user,deal])
				#put actor and ninja and deal back
			
			
			assert deal, 'Deal was not found'
			response = {
					'deal':api_utils.package_deal(deal)
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			self.send_error(e)
		except:
			self.send_fail()

class DownvoteHandler(api_utils.BaseHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs): #@UnusedVariable
		try:
			logging.debug('DOWNVOTE\n\n\n')
			logging.debug(kwargs)
			
			
			user 	= kwargs.get('actor')
#			uid 	= user.key()
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
				
				
			assert deal,'Deal could not be found'
			
			response = {
					'deal':api_utils.package_deal(deal)
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			self.send_error(e)
		except:
			self.send_fail()



class DeleteFavoriteHandler(api_utils.BaseHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		Input: uid
		response: {}
		'''
		try:
			logging.debug('DELETE FAVORITE\n\n\n')
			logging.debug(kwargs)
			
			user 	= kwargs.get('actor')
			deal 	= kwargs.get('deal')
			
#			uid 	= user.key()
			dealID 	= deal.key()
			
			
			#if the deal is in the users favorites, remove it. else do nothing
			if dealID in user.favorites:
				user.favorites.remove(dealID)
			
			#replace entities
			db.put(user)
			
			
			response = {}
			
			api_utils.send_response(self,response,user)
		except:
			self.send_fail()
		
		

class ReportHandler(api_utils.BaseHandler):
	@api_utils.validate('deal','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		Input: uid
		'''
		try:
			logging.debug("REPORT\n\n\n")
			logging.debug(kwargs)
			
			
			user	= kwargs.get('actor')
			deal	= kwargs.get('deal')
			
			uid		= user.key()
			dealID	= deal.key()
			
			#create report Entity
			levr.ReportedDeal(
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
			body += levr.log_model_props(user, ['email','display_name',''])
			body += str(user.email) +' is reporting '+str(deal.deal_text)
			message.body = body
			logging.debug(message.body)
			message.send()
			
			
			
			api_utils.send_response(self,{},user)
		except:
			self.send_fail()



class DealImgHandler(api_utils.BaseHandler):
	@api_utils.validate('deal',None,size=True)
	def get(self,*args,**kwargs):
		'''Returns ONLY an image for a deal specified by dealID
		Gets the image from the blobstoreReferenceProperty deal.img'''
		try:
			logging.info('IMAGE\n\n\n')
			logging.debug(kwargs)
			
			deal	= kwargs.get('deal')
			size	= kwargs.get('size')
			
			
			#get the blob
			blob_key = deal.img
			
			#send image to response output
			if not api_utils.send_img(self,blob_key,size):
				return
			
		except:
			levr.log_error()
			self.response.headers['Content-Type'] = 'image/jpeg'
			self.response.out.write(None)
			

class DealInfoHandler(api_utils.BaseHandler):
	@api_utils.validate('deal',None,
					user = False,
					levrToken = False
					)
	def get(self,*args,**kwargs):
		'''
		Get information about a deal.
		
		'''
		try:
			logging.debug('DEAL INFO\n\n\n')
			logging.debug(kwargs)
			deal	= kwargs.get('deal')
			private	= kwargs.get('private')
			
			assert deal, 'Deal could not be found'
			response = {
				'deal'	: api_utils.package_deal(deal,private)
			}
			api_utils.send_response(self,response)
		except AssertionError,e:
			self.send_error(e.message)
		except:
			self.send_fail()

class DealClickHandler(api_utils.BaseHandler):
	@api_utils.validate('deal','param',
					user=True,
					levrToken=True,
					query=True
					)
	def post(self,*args,**kwargs):
		'''
		@todo: Test 
		'''
#		user = kwargs.get('actor')
#		query = kwargs.get('query')
#		deal = kwargs.get('deal')
#		development = kwargs.get('development')
		
		try:
			### SPOOF ###
			query = 'Food'
			user = db.get(db.Key.from_path('Customer','pat'))
			deal = levr.Deal.all().get()
			### /SPOOF ###
			api_utils.KWLinker.register_like(deal, query)
			
		except:
			self.send_fail()
			
app = webapp2.WSGIApplication([ #('/api/deal/(.*)/redeem.*', RedeemHandler),
								#('/api/deal/(.*)/favorite.*', AddFavoriteHandler),
								('/api/deal/(.*)/upvote', UpvoteHandler),
								('/api/deal/(.*)/downvote', DownvoteHandler),
								('/api/deal/(.*)/deleteFavorite.*', DeleteFavoriteHandler),
								('/api/deal/(.*)/report.*', ReportHandler),
								('/api/deal/(.*)/img.*', DealImgHandler),
								('/api/deal/(.*)/click',DealClickHandler),
								('/api/deal/(.*)', DealInfoHandler)
								],debug=True)