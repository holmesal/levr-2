import webapp2
import logging


class RedeemHandler(webapp2.RequestHandler):
	def get(self,dealID):
		#RESTRICTED
		pass

class AddFavoriteHandler(webapp2.RequestHandler):
	def get(self,dealID):
		#RESTRICTED
		pass
		
class DeleteFavoriteHandler(webapp2.RequestHandler):
	def get(self,dealID):
		#RESTRICTED
		pass
		
class ReportHandler(webapp2.RequestHandler):
	def get(self,dealID):
		pass

class DealImgHandler(webapp2.RequestHandler):
	def get(self,dealID):
		pass

class DealInfoHandler(webapp2.RequestHandler):
	def get(self,dealID):
		self.response.out.write('Deal Info')
		
		
app = webapp2.WSGIApplication([('/api/deal/(.*)/redeem', RedeemHandler),
								('/api/deal/(.*)/addFavorite', AddFavoriteHandler),
								('/api/deal/(.*)/deleteFavorite', DeleteFavoriteHandler),
								('/api/deal/(.*)/report', ReportHandler),
								('/api/deal/(.*)/img', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)],debug=True)