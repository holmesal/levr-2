import webapp2
import logging
import api_utils
import api_utils_social as social
import levr_classes as levr
import levr_encrypt as enc
from random import randint
from google.appengine.ext import db
from google.appengine.api import urlfetch
import urllib
import json

def authorize(handler_method):
	'''
	Decorator checks the privacy level of the request.
	If the uid is valid and the user exists, it checks the levr_token to  privacy level
	
	'''
	def check(self,*args,**kwargs):
		try:
			logging.debug('PUBLIC OR PRIVATE DECORATOR\n\n\n')
#			logging.debug(levr.log_dir(self.request))
			logging.debug(args)
			logging.debug(kwargs)
			
			#CHECK USER
			uid = self.request.get('uid')
			if not api_utils.check_param(self,uid,'uid','key',True):
				raise Exception('uid: '+str(uid))
			else:
				uid = db.Key(enc.decrypt_key(uid))
			
			dealID = self.request.get('dealID')
			if not api_utils.check_param(self,dealID,'dealID','key',True):
				raise Exception('dealID: '+str(dealID))
			else:
				dealID = db.Key(enc.decrypt_key(dealID))
			
			#GET ENTITIES
			[user,deal] = db.get([uid,dealID])
			if not user or user.kind() != 'Customer':
				raise Exception('uid: '+str(uid))
			if not deal or deal.kind() != 'Deal':
				raise Exception('dealID: '+str(dealID))
			
			
			levr_token = self.request.get('levrToken')
			
			#if the levr_token matches up, then private request, otherwise public
			if user.levr_token == levr_token:
				private = True
			else:
				private = False
			
			logging.debug(private)
			
			
			kwargs.update({
						'user'	: user,
						'deal'	: deal,
						'private': private
						})
		except Exception,e:
			api_utils.send_error(self,'Invalid uid, '+str(e))
		else:
			handler_method(self,*args,**kwargs)
	
	return check

class ShareFacebookHandler(webapp2.RequestHandler):
	@authorize
#	@api_utils.private
	def get(self,*args,**kwargs):
		'''
		User shares on facebook
		inputs: uid, levrToken, dealID
		response: empty
		'''
		try:
			####
			#NOT DONE
			####
			user = kwargs.get('user')
			deal = kwargs.get('deal')
			logging.debug('\n\n\n\n')
			APP_ID = '448791615162217'
			APP_SECRET = '1db3af8377ccef564230ed62c27bbcc6'
			
#			facebook_token = user.facebook_token
			#debug
			facebook_token = 'AAAGYLHDMx2kBAB847zDPJmxJN4sfiiAsMDgL3lGACjmBJS7KOzzQmfP9V19YM7M9LIcghN3j8FJNT8UR8nDavZA8sfzO4ye8FWTZCBZAp9wZBVxxaYfZB'
			
			url = 'https://graph.facebook.com/me/levrinc:find'
			url += '?deal='+api_utils.create_share_url(deal)
			url += '&access_token='+facebook_token
			
			response = urlfetch.fetch(url=url)
			
			logging.debug(levr.log_dir(response))
			logging.debug(levr.log_dict(response.content))
			logging.debug(type(response.status_code))
			if response.status_code != 200:
				raise Exception(response.status_code)
			
#			self.response.out.write(api_utils.package_deal(deal))
			self.response.out.write(response.content)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')

app = webapp2.WSGIApplication([('/api/share/facebook', ShareFacebookHandler)
#								('/api/share/foursquare', ShareFoursquareHandler),
#								('/api/share/twitter', ShareTwitterHandler)
								],debug=True)