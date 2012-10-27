import os
import webapp2
import levr_classes as levr
import levr_encrypt as enc
#import levr_encrypt as enc
#import levr_utils
#from google.appengine.ext import db
import logging
import jinja2
import api_utils

#from gaesessions import get_current_session

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class ShareHandler(webapp2.RequestHandler):
	def get(self,identifier):
		try:
			logging.debug(identifier)
			deal = levr.Deal.all().filter('share_id =', identifier).get()
			
			if deal:
				logging.debug(deal)
				ninjaKey = deal.key().parent()
				ninja = levr.Customer.get(ninjaKey)
				#CHANGE THIS:
				#enc_key = enc.encrypt_key(str(deal.key()))
				enc_key = enc.encrypt_key(str(deal.key()))
				template_values = {
								'deal'	:api_utils.package_deal(deal),
								'ninja'	:ninja.display_name,
								'lat'	:deal.geo_point.lat,
								'lon'	:deal.geo_point.lon,
								'enc_key':enc_key
								}
				logging.debug(template_values)
				logging.debug(deal.__str__())
				template = jinja_environment.get_template('templates/share.html')
				self.response.out.write(template.render(template_values))
			else:
				template = jinja_environment.get_template('templates/shareError.html')
				self.response.out.write(template.render())
		except:
			levr.log_error()

app = webapp2.WSGIApplication([('/(.*)', ShareHandler)],
								debug=True)
