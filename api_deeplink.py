import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
from api_utils import private
from datetime import datetime
from google.appengine.ext import db
from google.appengine.api import taskqueue
import json
#from google.appengine.api import mail

class FloatingContentNewHandler(webapp2.RequestHandler):
	'''
	User is not logged into levr
	'''
	def get(self,*args,**kwargs):
		try:
			contentID = args[0]
			
			#spoof the contentID
			#contentID='85ff49d2dcb94b99973c5a2b16c5df36'
			
			#grab the associated floating content
			floating_content	=	levr.FloatingContent.gql('WHERE contentID=:1',contentID).get()
			
			action = floating_content.action
			response = {'action':action}
			
			if action == 'upload':
				#echo back the business
				response.update({'business':api_utils.package_business(floating_content.business)})
			elif action == 'deal':
				#echo bcak the deal
				packaged_deals = [api_utils.package_deal(floating_content.deal)]
				response.update({'deals':packaged_deals})
				
			#respond, and include levr_token
			response.update({'user':api_utils.package_user(floating_content.user,send_token=True)})
			
			api_utils.send_response(self,response)
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
class FloatingContentExistingHandler(webapp2.RequestHandler):
	'''
	User is logged into levr. I.e. case where uid and levrToken is available on phone
	'''
	@api_utils.validate('contentID','param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			#if we hit this handler it means that a user has both a levr account, and an account with the external service
			#we need to figure out which service (via the contentID prefix)
			#then, we need to figure out if we're dealing with two separate accounts
			#if so, we need to merge these two accounts and update references (are there any?)
			
			#grab and parse contentID to figure out what service the user has previously linked with
			
			logging.debug(kwargs)
			user = kwargs.get('user')
			contentID = kwargs.get('contentID')
			assert contentID,'contentID is not being passed'
#			contentID = args[0]
			service = contentID[0:3]
			#grab the floating content and the requesting user
			floating_content = levr.FloatingContent.gql('WHERE contentID=:1',contentID).get()
			donor = floating_content.user
			
			if service=='fou':
				logging.debug('The user came from foursquare')
				if user.foursquare_connected != True:
					#add the foursquare information from the donor to the levr user
					#create an instance of the Foursquare social connection class
					task_params = {
						'uid'	:	uid,
						'contentID'	: contentID,
						'service'	: 'foursquare'
					}
					t = taskqueue.add(url='/tasks/mergeUsersTask',payload=json.dumps(task_params))
					
			elif service=='fac':
				logging.debug('The user came from facebook')
				if user.facbook_connected != True:
					#merge these two users
					task_params = {
						'uid'	:	uid,
						'contentID'	: contentID,
						'service'	: 'facebook'
					}
					t = taskqueue.add(url='/tasks/mergeUsersTask',payload=json.dumps(task_params))
					#merge stuff hereeeee
			elif service=='twi':
				logging.debug('The user came from twitter')
				if user.twitter_connected != True:
					#merge these two users
					task_params = {
						'uid'	:	uid,
						'contentID'	: contentID,
						'service'	: 'twitter'
					}
					t = taskqueue.add(url='/tasks/mergeUsersTask',payload=json.dumps(task_params))
					#merge stuff hereeeee
			else:
				raise Exception('contentID prefix not recognized: '+service)
				
				
			#now that that fuckery is done with, grab and return the content requested
			action = floating_content.action
			response = {'action':action}
			
			if action == 'upload':
				#echo back the business
				response.update({'business':api_utils.package_business(floating_content.business)})
			elif action == 'deal':
				#echo bcak the deal
				packaged_deals = [api_utils.package_deal(floating_content.deal)]
				response.update({'deals':packaged_deals})
				
			#respond, including the token because why the hell not
			#response.update({'user':api_utils.package_user(user,send_token=True)})
			
			api_utils.send_response(self,response)
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
app = webapp2.WSGIApplication([('/api/deeplink/(.*)/new',FloatingContentNewHandler),
								('/api/deeplink/(.*)/existing',FloatingContentExistingHandler)
								],debug=True)