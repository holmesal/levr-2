from datetime import datetime
from google.appengine.api import urlfetch
from google.appengine.ext import db
import api_utils
import base64
import json
import levr_classes as levr
import logging
import urllib
import webapp2
#import levr_encrypt as enc
#import api_utils_social as social


class SearchFoursquareTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
				
				THE FOURSQUARE DEAL SEARCH TASK IS RUNNING
				
				''')
			
			
			
#  			logging.debug(self.request.body)
			payload = json.loads(self.request.body)
# 			logging.debug(payload)
			geo_point = db.GeoPt(payload['lat'],payload['lon'])
# 			logging.info(geo_point)
			foursquare_ids = payload['foursquare_ids']
# 			logging.info(foursquare_ids)
			#grab the token from the payload
			token = payload['token']
#			logging.info(token)
			deal_status = payload.get('deal_status','active')
# 			logging.info(levr.log_model_props(user))
			
			#foursquare stuff!
			ft1 = datetime.now()
#			logging.info('FOURSQUARE IDS::::')
#			logging.info(foursquare_ids)
#			logging.debug('searching foursquare () from a task!')
			foursquare_deals = api_utils.search_foursquare(geo_point,token,deal_status,foursquare_ids)
			logging.info('Foursquare results found: '+str(len(foursquare_deals)))
#			logging.info('Duplicates not put in database: '+str(len(foursquare_ids)))
			ft2 = datetime.now()
			logging.info('Foursquare action time: ' + str(ft2-ft1))
			
			
		except:
			levr.log_error()
			
class BusinessHarmonizationTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
			
			THE FOURSQUARE BUSINESS TASK IS RUNNING
			
			''')
			
			payload = json.loads(self.request.body)
			logging.debug(payload)
			
			geo_point = levr.geo_converter(payload['geo_str'])
			
			query = payload['query']
			
			key = payload['key']
			
			match = api_utils.match_foursquare_business(geo_point,query)
	
			logging.info(match)
			
			business = levr.Business.get(key)
			
			if match:
				logging.info('Foursquare ID found: '+match['foursquare_id'])
				
				#are there any previously added foursquare businesses?
				#q_orphans = levr.Business.gql('WHERE foursquare_id=:1',match['foursquare_id'])
				
				#grab a duplicate business
				duplicate_business = levr.Business.gql('WHERE foursquare_id=:1',match['foursquare_id']).get()
				
				if duplicate_business:
					#grab all the deal keys from that business
					keys = levr.Deal.gql('WHERE businessID = :1',str(duplicate_business.key())).fetch(None,keys_only=True)
					duplicate_business.delete()
					logging.debug('DELETED ORIGINAL FOURSQUARE BUSINESS')
				
				#update business entity
				business.foursquare_id = match['foursquare_id']
				business.foursquare_name = match['foursquare_name']
				business.foursquare_linked	=	True
				business.put()
				
				for key in keys:
					deal = db.get(key)
					deal.businessID = str(business.key())
					deal.put()
					logging.debug('UPDATED DEAL BUSINESSID')
				
			else:
				#update to show notfound
				logging.info('No foursquare match found.')
				
				
			#go grab all the deals and update
			
		except:
			levr.log_error()
				
class FoursquareDealUpdateTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
			
			THE FOURSQUARE DEAL UPDATE TASK IS RUNNING
			
			''')
			
			payload = json.loads(self.request.body)
			
			foursquare_id = payload['foursquare_id']
			deal_id = payload['deal_id']
			uid = payload['uid']
			token =  payload['token']
			deal_status = payload['deal_status']
			
			logging.info('This task was started by a user/deal with the following information:')
			logging.info('UID: '+uid)
			logging.info('Foursquare user token: '+token)
			logging.info('Reported deal ID: '+deal_id)	
			logging.info('Business foursquare ID: '+foursquare_id)
			logging.info('deal_status: '+deal_status)
			
			api_utils.update_foursquare_business(foursquare_id,deal_status,token)
			
			
		except:
			levr.log_error()
				
class NewUserTextTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			
			logging.info('''
				
				SKYNET IS TEXTING THE FOUNDERS
				
				''')
			
			payload = json.loads(self.request.body)
			
			#twilio credentials
			sid = 'AC4880dbd1ff355288728be2c5f5f7406b'
			token = 'ea7cce49e3bb805b04d00f76253f9f2b'
			twiliourl='https://api.twilio.com/2010-04-01/Accounts/AC4880dbd1ff355288728be2c5f5f7406b/SMS/Messages.json'
			
			auth_header = 'Basic '+base64.b64encode(sid+':'+token)
			logging.info(auth_header)
			
			numbers = ['+16052610083','+16035605655']
			
			for number in numbers:
				request = {'From':'+16173608582',
							'To':number,
							'Body':'Awwwww yeeeaahhhhh. You have a new user: '+payload['user_string']}
			
			result = urlfetch.fetch(url=twiliourl,
								payload=urllib.urlencode(request),
								method=urlfetch.POST,
								headers={'Authorization':auth_header})
								
			logging.info(levr.log_dict(result.__dict__))
			
		except:
			levr.log_error()
			
class MergeUsersTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			
			logging.info('''
				
				THE MERGE USERS TASK IS RUNNING
				
				''')
			
			payload = json.loads(self.request.body)
			
			uid = payload['uid']
			contentID = payload['contentID']
			service = payload['service']
			
			#grab the user
			user = levr.Customer.get(uid)
			#grab the donor's foursquare token
			floating_content = levr.FloatingContent.gql('WHERE contentID=:1',contentID).get()
			donor = floating_content.user
			
			api_utils.merge_customer_info_from_B_into_A(user,donor,service)
			
		except:
			levr.log_error()
			
class RotateImageHandler(webapp2.RequestHandler):
	def post(self):
		pass
		

app = webapp2.WSGIApplication([('/tasks/searchFoursquareTask', SearchFoursquareTaskHandler),
								('/tasks/businessHarmonizationTask', BusinessHarmonizationTaskHandler),
								('/tasks/foursquareDealUpdateTask', FoursquareDealUpdateTaskHandler),
								('/tasks/newUserTextTask', NewUserTextTaskHandler),
								('/tasks/mergeUsersTask', MergeUsersTaskHandler)
								],debug=True)