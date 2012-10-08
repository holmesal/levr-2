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
			logging.info('THE TASK IS RUNNING')
			logging.info('THE TASK IS RUNNING')
			logging.info('THE TASK IS RUNNING')
			logging.info('THE TASK IS RUNNING')
			logging.info('THE TASK IS RUNNING')
			logging.info('THE TASK IS RUNNING')
			
# 			logging.info(self.request.body)
			payload = json.loads(self.request.body)
# 			logging.info(payload)
			geo_point = db.GeoPt(payload['lat'],payload['lon'])
# 			logging.info(geo_point)
			userID = payload['userID']
# 			logging.info(userID)
			foursquare_ids = payload['foursquare_ids']
# 			logging.info(foursquare_ids)
			
			#grab user
			user = levr.Customer.get(userID)
# 			logging.info(levr.log_model_props(user))
			
			#foursquare stuff!
			ft1 = datetime.now()
			logging.info('FOURSQUARE IDS::::')
			logging.info(foursquare_ids)
			logging.debug('searching foursquare () from a task!')
			foursquare_deals = api_utils.search_foursquare(geo_point,user,foursquare_ids)
			logging.info('Foursquare results found: '+str(len(foursquare_deals)))
			logging.info('Duplicates not put in database: '+str(len(foursquare_ids)))
			ft2 = datetime.now()
			logging.info('Foursquare action time: ' + str(ft2-ft1))
			
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class BusinessHarmonizationTaskHandler(webapp2.RequestHandler):
		def post(self):
			try:
				logging.info('''THE FOURSQUARE BUSINESS TASK IS RUNNING
				
				
				''')
				
				payload = json.loads(self.request.body)
				
				geo_point = levr.geo_converter(payload['geo_str'])
				
				query = payload['query']
				
				key = payload['key']
				
				match = api_utils.match_foursquare_business(db.GeoPt(42.16617,-72.54514982),'no_match')
		
				logging.info(match)
				
				if match:
					logging.info('Foursquare ID found: '+match)
					#update business entity
					business = levr.Business.get(key)
					business.foursquare_id = match
					business.put
				else:
					logging.info('No foursquare match found.')
				
			except:
				levr.log_error()
				api_utils.send_error(self,'Server Error')	
		

app = webapp2.WSGIApplication([('/tasks/searchFoursquareTask', SearchFoursquareTaskHandler),
								('/tasks/businessHarmonizationTask', BusinessHarmonizationTaskHandler)
								],debug=True)