import os
import webapp2
import jinja2
import logging
from google.appengine.api import mail
import random
from datetime import datetime
import api_utils
from google.appengine.ext import db

class landing(webapp2.RequestHandler):
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
			
		#version = 'android'
		
		#TODO:
		#grab deals from a few specific geohashes that cover boston
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
		

		template_values = {
			'deals'		: packaged_deals,
			'version'	: version
		}
		
		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/landing_v4.html')
		self.response.out.write(template.render(template_values))

		
	def post(self):
			logging.info(self.request.get('email'))
			#message to user
			message = mail.EmailMessage(
				sender	="Levr <beta@levr.com>",
				subject	="Your Levr Beta Request",
				to		=self.request.get('email'))
			logging.debug(message)
			html = '''<html><body style="background-color: #f3f3f3; margin:0; font-family: helvetica, arial,sans-serif;">
	<div style="background-color: white; width: 80%; margin-left: auto; margin-right: auto; height:auto; margin-top: 15px; margin-bottom: 15px;">
		<div style="padding:20px;">
			<p style="font-size: 20pt; font-weight: 300; text-align:center;">Welcome to Levr Beta.</p>
			<p style="font-size: 15pt; font-weight: 300; margin-top: 50px;">On behalf of the Levr team, it's great to have you aboard.</p>
			<p style="font-size: 15pt; font-weight: 300;">We're sending out invitations on a first-come, first-serve basis. We've reserved you a spot in line, and we'll let you know as soon as you can download Levr.</p>
			<p style="font-size: 15pt; font-weight: 300;">In the meantime, feel free to keep up with us via our <a href="http://blog.levr.com">blog</a>, or shout at us on <a href="http://twitter.com/getlevr">twitter</a>.</p>
			<p style="font-size: 15pt; font-weight: 300; margin-top: 50px;">See you soon!</p>
			<p style="font-size: 15pt; font-weight: 300;">-Levr</p>
		</div>
	</div>
</body></html>'''
			message.html = html
			body = '''
			Welcome to Levr Beta.
			
			On behalf of the Levr team, it's great to have you aboard.
			
			We're sending out invitations on a first-come, first-serve basis. We've reserved you a spot in line, and we'll let you know as soon as you can download Levr.
			
			In the meantime, feel free to keep up with us via our blog (http://blog.levr.com), or shout at us on twitter (http://twitter.com/getlevr).
			
			See you soon!
			-Levr'''
			message.body = body
			message.send()
			
			#message to alonso
			message = mail.EmailMessage(
				sender	="Levr <beta@levr.com>",
				subject	="New beta user",
				#to		=self.request.get('email'))
				to		='<beta@levr.com>')
			logging.debug(message)
			body = 'New beta request from email: ' + self.request.get('email')
			message.body = body
			message.send()
			#self.response.out.write(message.body)
	

app = webapp2.WSGIApplication([('/', landing)],debug=True)