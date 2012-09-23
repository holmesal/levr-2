import webapp2
import logging
import api_utils
import levr_classes as levr
import levr_encrypt as enc


class ConnectFacebookHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		#check uid
		uid	= self.request.get('uid')
		if uid == '':
			api_utils.send_error(self,'Required parameter not passed: uid')
			return
		
		#decrypt uid
		try:
			uid = enc.decrypt_key(uid)
			uid = db.Key(uid)
		except:
			api_utils.send_error(self,'Invalid parameter: uid')
			return

class ConnectFoursquareHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		
class ConnectTwitterHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return
		
class ConnectLevrHandler(webapp2.RequestHandler):
	def get(self):
		#RESTRICTED
		
		#check token
		token = self.request.get('token')
		if token == '':
			api_utils.send_error(self,'Required parameter not passed: token')
			return	
		
app = webapp2.WSGIApplication([('/api/connect/facebook', ConnectFacebookHandler),
								('/api/connect/foursquare', ConnectFoursquareHandler),
								('/api/connect/twitter', ConnectTwitterHandler),
								('/api/connect/levr', ConnectLevrHandler)],debug=True)