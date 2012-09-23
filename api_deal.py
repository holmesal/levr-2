import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
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
		try:
			uid = self.request.params['uid']
			logging.info(uid)
			#get inputs
			if not uid:
				api_utils.send_error(self,'Required Parameter not passed: uid')
				return
			try:
				uid = db.Key(uid)
			except:
				api_utils.send_error(self,': uid')
			try:
				dealID = db.Key(dealID)
			except:
				api_util.send_error(self,'Invalid input: dealID')
			
			
			#get user entity
			user		= levr.Customer.get(uid)
			if not user:
				api_utils.send_error(self,'Invalid uid: %s',uid)
			
			#append dealID to favorites property
			user.favorites.append(db.Key(dealID))
			logging.debug(user.favorites)
	#				
			#get notifications
			notifications = user.get_notifications()
			
			#close entity
			user.put()
			api_utils.send_response(self,{})
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'')
		
		
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
								('/api/deal/(.*)/addfavorite', AddFavoriteHandler),
								('/api/deal/(.*)/deletefavorite', DeleteFavoriteHandler),
								('/api/deal/(.*)/report', ReportHandler),
								('/api/deal/(.*)/img', DealImgHandler),
								('/api/deal/(.*)', DealInfoHandler)
								],debug=True)