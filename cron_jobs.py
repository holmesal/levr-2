from datetime import datetime
from google.appengine.ext import db
import api_utils
import json
import levr_classes as levr
import levr_encrypt as enc
import logging
import random
import webapp2
				
class FoursquareDealUpdateHandler(webapp2.RequestHandler):
		def get(self):
			try:
				logging.info('''
				
				THE FOURSQUARE DEAL UPDATE CRON JOB IS RUNNING
				
				''')
				
				#go grab all the foursquare businesses we have on the platform
				foursquare_businesses = levr.Business.gql('WHERE foursquare_linked = :1',True)
				
				for foursquare_business in foursquare_businesses:
					try:
						logging.info('''
						
							Updating the deals at the following business:
							
						''')
						logging.info(foursquare_business.business_name)
						logging.info(foursquare_business.key())
						logging.info(foursquare_business.foursquare_id)
						api_utils.update_foursquare_business(foursquare_business.foursquare_id,'random')
					except:
						levr.log_error()	
					
				
				
				# payload = json.loads(self.request.body)
# 				
# 				foursquare_id = payload['foursquare_id']
# 				deal_id = payload['deal_id']
# 				uid = payload['uid']
# 				token =  payload['token']
# 				
# 				logging.info('This task was started by a user/deal with the following information:')
# 				logging.info('UID: '+uid)
# 				logging.info('Foursquare user token: '+token)
# 				logging.info('Reported deal ID: '+deal_id)	
# 				logging.info('Business foursquare ID: '+foursquare_id)	
# 				
# 				
# 				logging.info('')		
# 				
# 				api_utils.update_foursquare_business(foursquare_id,token)
				
				
			except:
				levr.log_error()
class UndeadLikesStuffHandler(webapp2.RequestHandler):
	def get(self):
		logging.info('\n\n\n\t\t\t THE UNDEAD HAVE RISEN AND ARE LIKING STUFF! \n\n\n')
		try:
			#grab random ninja
			#grab random deal
			#rando ninja likes rando deal
			user = levr.get_random_dead_ninja()
			
			deals = levr.Deal.all(keys_only=True).fetch(None)
			
			#select random deal from deals
			deal = random.choice(deals)
			
			dealID = deal.key()
			uid = user.key()
			
			
			
			#===================================================================
			# Note: this code is copied from /deal/<dealID>/upvote
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
			
			
			
		except:
			levr.log_error()



app = webapp2.WSGIApplication([('/cronjobs/foursquareDealUpdate', FoursquareDealUpdateHandler),
							('/cronjobs/undeadActivity', UndeadLikesStuffHandler)
								],debug=True)