#from google.appengine.api import urlfetch
#import api_utils
#import levr_classes as levr
#import logging
#import webapp2
##from google.appengine.ext import db
##import levr_encrypt as enc
##import api_utils_social as social
##from random import randint
##import urllib
##import json
#
#class ShareFacebookHandler(webapp2.RequestHandler):
##	@authorize
##	@api_utils.private
#	def get(self,*args,**kwargs):
#		'''
#		User shares on facebook
#		inputs: uid, levrToken, dealID
#		response: empty
#		'''
#		try:
#			####
#			#NOT DONE
#			####
#			user = kwargs.get('user')
#			deal = kwargs.get('deal')
#			logging.debug('\n\n\n\n')
#			APP_ID = '448791615162217'
#			APP_SECRET = '1db3af8377ccef564230ed62c27bbcc6'
#			
##			facebook_token = user.facebook_token
#			#debug
#			facebook_token = 'AAAGYLHDMx2kBAB847zDPJmxJN4sfiiAsMDgL3lGACjmBJS7KOzzQmfP9V19YM7M9LIcghN3j8FJNT8UR8nDavZA8sfzO4ye8FWTZCBZAp9wZBVxxaYfZB'
#			
#			url = 'https://graph.facebook.com/me/levrinc:find'
#			url += '?deal='+api_utils.create_share_url(deal)
#			url += '&access_token='+facebook_token
#			
#			response = urlfetch.fetch(url=url)
#			
#			logging.debug(levr.log_dir(response))
#			logging.debug(levr.log_dict(response.content))
#			logging.debug(type(response.status_code))
#			if response.status_code != 200:
#				raise Exception(response.status_code)
#			
##			self.response.out.write(api_utils.package_deal(deal))
#			self.response.out.write(response.content)
#		except:
#			levr.log_error()
#			api_utils.send_error(self,'Server Error')
#
#app = webapp2.WSGIApplication([('/api/share/facebook', ShareFacebookHandler)
##								('/api/share/foursquare', ShareFoursquareHandler),
##								('/api/share/twitter', ShareTwitterHandler)
#								],debug=True)