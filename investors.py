import os
import webapp2
import jinja2
import logging
from google.appengine.api import mail
import random
from datetime import datetime
import api_utils
from google.appengine.ext import db

class InvestorsHandler(webapp2.RequestHandler):
	def get(self):
	
		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/landing-investors-v5.html')
		self.response.out.write(template.render())

app = webapp2.WSGIApplication([('/investors', InvestorsHandler)],debug=True)