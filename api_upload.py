import os
import webapp2
import jinja2
import logging


class UploadRequestHandler(webapp2.RequestHandler):
	def get(self):
		pass

class UploadPostHandler(webapp2.RequestHandler):
	def get(self):
		pass
		
		
app = webapp2.WSGIApplication([('/api/upload/request', UploadRequestHandler),
								('/api/upload/post', UploadPostHandler)],debug=True)