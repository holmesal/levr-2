import webapp2
import logging

'''
DEAL OBJECT :{
			#PUBLIC
			dealID:
			business:{
					businessID:
					businessName:
					vicinity:
					geoPoint:
					geoHash:
					}
			dealText:
			description:
			shareURL: URL
			geoPoint:
			geoHash:
			status:
			largeImg: URL
			smallImg: URL
			dateUploaded:
			dateEnd:
			isExclusive: bool
			barcode: None if empty
			redemptions: number
			tags: [list]
			#PRIVATE
			
			}
USER OBJECT :{
			#PUBLIC
			uid:
			alias:
			}
'''

class RedeemHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		inputs: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		#RESTRICTED

class AddFavoriteHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		#RESTRICTED
		pass
		
class DeleteFavoriteHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		#RESTRICTED
		pass
		
class ReportHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: uid
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		pass

class DealImgHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: None
		Output:{
			meta:{
				success
				errorMsg
				}
		'''
		pass

class DealInfoHandler(webapp2.RequestHandler):
	def get(self,dealID):
		'''
		Input: None
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				<DEAL OBJECT>
				}
			}
		'''
		self.response.out.write('Deal Info')
		
		
app = webapp2.WSGIApplication([('/api/deal/(.*)/redeem', RedeemHandler),
								('/api/deal/(.*)/addFavorite', AddFavoriteHandler),
								('/api/deal/(.*)/deleteFavorite', DeleteFavoriteHandler),
								('/api/deal/(.*)/report', ReportHandler),
								('/api/deal/(.*)/img', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)
								],debug=True)