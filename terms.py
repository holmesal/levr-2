import os
import webapp2
import jinja2
import logging
from google.appengine.api import mail
import random
from datetime import datetime
import api_utils
from google.appengine.ext import db

class TermsHandler(webapp2.RequestHandler):
	def get(self):
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/terms.html')
		self.response.out.write(template.render())
	

app = webapp2.WSGIApplication([('/terms', TermsHandler)],debug=True)