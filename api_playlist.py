import api_utils
import levr_classes as levr
import levr_encrypt as enc
import logging
import webapp2

class PlaylistDistributorHandler(api_utils.BaseHandler):
	@api_utils.validate('query',None)
	def get(self,*args,**kwargs):
		playlist_name = kwargs.get('query')
		try:
			pass
			
		except:
			self.send_fail()
app = webapp2.WSGIApplication([
								('/api/playlist/(.*)',PlaylistDistributorHandler),
								],debug=True)