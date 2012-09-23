import os
import webapp2
import jinja2
import logging


class RedeemHandler(webapp2.RequestHandler):
	def get(self,uid):
		self.response.out.write('Redeem')

class AddFavoriteHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass
		
class DeleteFavoriteHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass
		
class ReportHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass

class DeleteFavoriteHandler(webapp2.RequestHandler):
	def get(self,uid):
		pass

class DealInfoHandler(webapp2.RequestHandler):
	def get(self,uid):
		self.response.out.write('Deal Info')
		
		
app = webapp2.WSGIApplication([('/api/deal/(.*)/redeem', RedeemHandler),
								('/api/deal/(.*)/addFavorite', AddFavoriteHandler),
								('/api/deal/(.*)/deleteFavorite', DeleteFavoriteHandler),
								('/api/deal/(.*)/report', ReportHandler),
								('/api/deal/(.*)/img', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)],debug=True)