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
class ExpireDealsHandler(webapp2.requestHandler):
	'''
	A cron job to expire deals that are more than 7 days old
	'''
	def get(self):
		try:
			now = datetime.now()
			
			#fetch all deals that are set to expire
			deals = levr.Deal.all().filter('deal_status','active').filter('date_end <=',now).fetch(None)
			
			#set deal_status to expired
			for deal in deals:
				#set expired deal status
				deal.deal_status = 'expired'
				#grab the deal owner
				to_be_notified = deal.key().parent()
				#create the notification
				levr.create_notification('expired',to_be_notified,None,deal.key())
			#replace deals
			db.put(deals)
			
		except:
			levr.log_error()



app = webapp2.WSGIApplication([('/cronjobs/foursquareDealUpdate', FoursquareDealUpdateHandler),
							('/cronjobs/expireDeals', ExpireDealsHandler)
								],debug=True)