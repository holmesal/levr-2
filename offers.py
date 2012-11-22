import os
import webapp2
import jinja2
import logging
from google.appengine.api import mail
import random
from datetime import datetime
import api_utils
from google.appengine.ext import db

class OffersHandler(webapp2.RequestHandler):
	def get(self):
		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		
		#check user-agent to see if user is mobile or not
		#get the user-agent
# 		uastring = str(self.request.headers['user-agent'])
		
# 		logging.info(uastring)
		
		#same template for mobile and desktop (for now)
		# if 'Mobile' in uastring:
# 			if 'iPad' in uastring:
# 				logging.info('THIS IS AN iPad')
# 				#serve desktop landing page
# 				template = jinja_environment.get_template('templates/landing_v3.html')
# 			else:
# 				logging.info('THIS IS A MOBILE DEVICE')
# 				#serve mobile landing page
# 				template = jinja_environment.get_template('templates/landing_v3.html')
# 		else:
# 			logging.info('THIS IS A DESKTOP DEVICE')
# 			#serve desktop landing page
# 			template = jinja_environment.get_template('templates/landing_v3.html')
		
		#choices = ['Version A','Version B']
		#version = random.choice(choices)
		
# 		version = 'Version B'
# 		
# 		logging.info('Serving: '+version)
# 		template_values = {
# 			"version"	:	version
# 		}
# 		
# 		if version == 'Version A':
# 			template_values.update({'css':'landing_v3_version_a'})
# 		elif version == 'Version B':
# 			template_values.update({'css':'landing_v3_version_b'})
# 		
# 		template = jinja_environment.get_template('templates/landing_v3_final.html')
# 		self.response.out.write(template.render(template_values))

		uastring = str(self.request.headers['user-agent'])
	
		logging.info(uastring)
			
		if 'iphone' in uastring.lower():
			version = 'iPhone'
			logging.debug('Serving mobile version - iPhone')
		elif 'android' in uastring.lower():
			version = 'android'
			logging.debug('Serving mobile version - android')
		else:
			version = 'desktop'
			logging.debug('Serving desktop version')
		
		logging.info(self.request.get('city'))
		
		city = self.request.get('city')
		logging.info(city)
		
		if city == 'sanfrancisco':
			#huge san francisco geohashes (+ palo alto)
			geo_hash_set = ['9q8z','9q8y','9q8v','9q8p','9q8n','9q8j','9q9h']
		else:
			#huge boston geohashes
			geo_hash_set = ['drt3','drmr','drt8','drt0','drt1','drt9','drmx','drmp','drt2']
		
		logging.debug('\n\n\n \t\t\t START QUERYING \n\n\n')
		query_start = datetime.now()
		deal_keys = api_utils.get_deal_keys(geo_hash_set)
		query_end = datetime.now()
		
		total_query_time = query_end-query_start
		
		logging.debug('\n\n\n \t\t\t END QUERYING \n\n\n ')
		
		logging.info('Query time: '+str(total_query_time))
		
		deals = db.get(deal_keys)
		
		sorted_deals = []
		#remove the non-active and foursquare deals
		for deal in deals:
			logging.debug(deal.deal_status)
			if deal.deal_status in ['active']:
				logging.debug(deal.origin)
				if deal.origin in ['levr','merchant']:
					sorted_deals.append(deal)
				else:
					logging.info('deal not added because origin was: '+deal.origin)
			else:
				logging.info('deal not added because status was:' +deal.deal_status)
		
		packaged_deals = api_utils.package_deal_multi(sorted_deals)
		
# 		logging.info(packaged_deals)
		
		#go through and swap lat and lon
		for deal in packaged_deals:
			logging.info(deals)
			#separate lat and lon
			deal['lat'] = deal['business']['geoPoint'].split(',')[0]
			deal['lon'] = deal['business']['geoPoint'].split(',')[1]
			#fix image url
			deal['imgURL'] = deal['largeImg'].split('?')[0]+'?size=webMapView'
			deal['description'] = deal['description'].replace('\n',' ')
		

		template_values = {
			'deals'		: packaged_deals,
			'version'	: version,
			'city'		: city
		}
		
		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/landing_v4.html')
		self.response.out.write(template.render(template_values))
		
app = webapp2.WSGIApplication([('/offers', OffersHandler)],debug=True)