import webapp2
import logging
import levr_classes as levr
import levr_encrypt as enc
import api_utils
import json
from google.appengine.ext import db
from datetime import datetime


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
			logging.info(token)
			
# 			logging.info(levr.log_model_props(user))
			
			#foursquare stuff!
			ft1 = datetime.now()
			logging.info('FOURSQUARE IDS::::')
			logging.info(foursquare_ids)
			logging.debug('searching foursquare () from a task!')
			foursquare_deals = api_utils.search_foursquare(geo_point,token,foursquare_ids)
			logging.info('Foursquare results found: '+str(len(foursquare_deals)))
			logging.info('Duplicates not put in database: '+str(len(foursquare_ids)))
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
					business.foursquare_id = 'not_harmonized'
					business.foursquare_name = 'not_harmonized'
					business.put()
				
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
		

app = webapp2.WSGIApplication([('/tasks/searchFoursquareTask', SearchFoursquareTaskHandler),
								('/tasks/businessHarmonizationTask', BusinessHarmonizationTaskHandler),
								('/tasks/foursquareDealUpdateTask', FoursquareDealUpdateTaskHandler)
								],debug=True)