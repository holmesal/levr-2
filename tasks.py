import webapp2
import logging
import levr_classes as levr
import levr_encrypt as enc
import api_utils
import json
from google.appengine.ext import db
from datetime import datetime
import base64
from google.appengine.api import urlfetch
import urllib
import api_utils_social as social


class SearchFoursquareTaskHandler(webapp2.RequestHandler):
	def post(self):
		try:
			logging.info('''
				
				THE FOURSQUARE DEAL SEARCH TASK IS RUNNING
				
				''')
			
# 			logging.info(self.request.body)
			payload = json.loads(self.request.body)
# 			logging.info(payload)
			geo_point = db.GeoPt(payload['lat'],payload['lon'])
# 			logging.info(geo_point)
			foursquare_ids = payload['foursquare_ids']
# 			logging.info(foursquare_ids)
			#grab the token from the payload
			token = payload['token']
#			logging.info(token)
			
# 			logging.info(levr.log_model_props(user))
			
			#foursquare stuff!
			ft1 = datetime.now()
#			logging.info('FOURSQUARE IDS::::')
#			logging.info(foursquare_ids)
#			logging.debug('searching foursquare () from a task!')
			foursquare_deals = api_utils.search_foursquare(geo_point,token,foursquare_ids)
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
				
				geo_point = levr.geo_converter(payload['geo_str'])
				
				query = payload['query']
				
				key = payload['key']
				
				match = api_utils.match_foursquare_business(db.GeoPt(42.16617,-72.54514982),query)
		
				logging.info(match)
				
				business = levr.Business.get(key)
				
				if match:
					logging.info('Foursquare ID found: '+match)
					#update business entity
					business.foursquare_id = match['foursquare_id']
					business.foursquare_name = match['foursquare_name']
					business.foursquare_linked	=	True
					business.put()
				else:
					#update to show notfound
					logging.info('No foursquare match found.')
				
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
				
				logging.info('This task was started by a user/deal with the following information:')
				logging.info('UID: '+uid)
				logging.info('Foursquare user token: '+token)
				logging.info('Reported deal ID: '+deal_id)	
				logging.info('Business foursquare ID: '+foursquare_id)			
				
				api_utils.update_foursquare_business(foursquare_id,token)
				
				
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
			
			if service=='foursquare':
				logging.info('The user came from foursquare')
				user = social.Foursquare(user,'verbose')
				#connect the user using foursquare
				new_user, new_user_details, new_friends = user.first_time_connect(
										foursquare_token=donor.foursquare_token
										)
			elif service=='facebook':
				logging.info('The user came from facebook')
				user = social.Facebook(user,'verbose')
				#connect the user using facebook
				new_user, new_user_details, new_friends = user.first_time_connect(
										facebook_token=donor.facebook_token
										)
			elif service=='twitter':
				logging.info('The user came from twitter')
				user = social.Twitter(user,'verbose')
				#connect the user using facebook
				new_user, new_user_details, new_friends = user.first_time_connect(
										twitter_token=donor.twitter_token
										)
			else:
				raise Exception('contentID prefix not recognized: '+service)
		
		except:
			levr.log_error()
		

app = webapp2.WSGIApplication([('/tasks/searchFoursquareTask', SearchFoursquareTaskHandler),
								('/tasks/businessHarmonizationTask', BusinessHarmonizationTaskHandler),
								('/tasks/foursquareDealUpdateTask', FoursquareDealUpdateTaskHandler),
								('/tasks/newUserTextTask', NewUserTextTaskHandler),
								('/tasks/mergeUsersTask', MergeUsersTaskHandler)
								],debug=True)