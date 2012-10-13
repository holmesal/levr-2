from google.appengine.api import urlfetch
import api_utils
import api_utils_social as social
import jinja2
import json
import levr_classes as levr
import levr_utils
import logging
import os
import urllib
import webapp2
from social_data import facebook_auth
import uuid
#import levr_encrypt as enc
#import levr_utils
#from google.appengine.ext import db


#CASES:

#1 - User checks in, we don't have that business in our database
	#Response: Hey, there are 10 offers near you (deeplink to dealResults)
	#Response: Hey, you should be the first to upload an offer (only for some types of establishments) (deeplink to deal upload)
#2 - User checks in, we have the business, we don't have any deals there
	#Response: same as above
#3 - User checks in, we have the business, we have one deal there
	#Response: Hey check out this deal! {{DEALTEXT}}(deeplink to dealDetail)
#4 - User checks in, we have the business, we have more than one deal there
	#Response: Hey, check out {{DEALTEXT}}(deeplink to dealDetail) and 5 more deals(deeplink to dealResults)


class AuthorizeBeginHandler(webapp2.RequestHandler):
	def get(self):
		logging.debug('\n\n\t\t Hit the Authorize Begin Handler \n\n')
		client_id		= facebook_auth['client_id']
		state			= uuid.uuid4()
		scope			= 'publish_actions'
		redirect_uri	= 'http://levr-production.appspot.com/facebook/authorize/exchange'
		url = 'https://www.facebook.com/dialog/oauth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={scope}'.format(
													client_id = client_id, redirect_uri= redirect_uri, scope= scope, state= state)
		logging.debug(url)
		self.redirect(url)
class ExchangeCodeHandler(webapp2.RequestHandler):
	def get(self):
		logging.debug('\n\n\t\t Exchange code param with facebook for auth stuff \n\n')
		client_id = facebook_auth['client_id']
		client_secret = facebook_auth['client_secret']
		
		#=======================================================================
		# get response params
		#=======================================================================
		
		#check for error
		error = self.request.get('error',None)
		assert error == None, 'User denied request'
		
		state = self.reqest.get('state',None)
		code = self.request.get('code',None)
		logging.debug(state)
		logging.debug(code)
		#make sure code has proper appendage
		assert code[-4:] == '#_=_'
		#remove appended #_=_ from the code
		code = code[:-4]
		
		#=======================================================================
		# Redirect back to Facebook
		#=======================================================================
		redirect_uri = 'http://levr-production.appspot.com/facebook.authorize/complete'
		
		url = 'https://graph.facebook.com/oauth/access_token?client_id={client_id}&redirect_uri={redirect_uri}&client_secret={client_secret}&code={code}'.format(
															 client_id= client_id, redirect_uri= redirect_uri, client_secret= client_secret, code= code)
		self.redirect(url)
		
class AuthorizeCompleteHandler(webapp2.RequestHandler):
	def get(self):
		logging.debug('Hit the Authorize Complete Handler')
		
		#=======================================================================
		# Get values
		#=======================================================================
		facebook_token = self.request.get('access_token')
		expires = self.request.get('expires')
		#create a levr token
		
		#=======================================================================
		# Create the user and connect them
		#=======================================================================
		#create the user here
		user = levr.Customer(levr.create_levr_token())
		user.put()
		
		#wrap the user in the social class
		user = social.Facebook(user)
		
		user,new_details,new_friends = user.first_time_connect(facebook_token=facebook_token)
		
		logging.debug(levr.log_model_props(user))
		logging.debug(levr.log_dict(new_details))
		logging.debug(levr.log_dict(new_friends))
		
		
		#send the founders a text
		levr.text_notify(user.first_name + ' ' + user.last_name + ' from foursquare')
		
		#set up the jinja template and echo out
		template = jinja_environment.get_template('templates/deal.html')
		self.response.out.write(template.render(template_values))
		
		logging.debug(levr.log_dict(user))

class PushHandler(webapp2.RequestHandler):
	def post(self):
		logging.debug('Foursquare push request received!')
		logging.debug(self.request.body)
		checkin = json.loads(self.request.get('checkin'))
		secret = self.request.get('secret')
		logging.debug(checkin)
		
		#verify that the secret passed matches ours
		hc_secret = 'VLKDNIT0XSA5FK3XIO05DAWVDVOXTSUHPE4H4WOHNIZV14G3'
		if hc_secret != secret:
			#raise an exception
			logging.debug('SECRETS DO NOT MATCH')
		
		#go look in our database for a matching foursquare venue id
		business = levr.Business.gql('WHERE foursquare_id = :1',checkin["venue"]["id"]).get()
		#business = levr.Business.get('ahFzfmxldnItcHJvZHVjdGlvbnIQCxIIQnVzaW5lc3MY-dIBDA')
		
		#initialize the response object
		reply = {
			'CHECKIN_ID'		: checkin['id'],
			'text'				: 'Hi there! We seem to be having some issues. Back soon!',
			'url'				: 'http://www.levr.com',
			'contentID'			: 'BWANHHPAHAHA'
		}
		'''
		if business:	#business found
			#for deal in levr.Deal().all().filter('businessID =', str(business.key())).run():
			q = levr.Deal.gql("WHERE businessID = :1 AND deal_status = :2 ORDER BY count_redeemed DESC",str(business.key()),'active')
			numdeals = q.count()
			if numdeals > 1:	#many deals found
				topdeal = q.get()
				reply['text'] = "There are "+str(numdeals)+" deals here! Click to browse."
				reply['url'] = '' #deeplink into dealResults screen
			elif numdeals == 1:	#only one deal found
				topdeal = q.get()
				reply['text'] = topdeal.deal_text+". Click to redeem."
				reply['url'] = '' #deeplink into dealDetail screen
			else:	#no deals found
				reply['text'] = "See any deals? Pay it forward: click to upload."
				reply['url'] = '' #deeplink into deal upload screen
		else:			#no business found
			#ask pat for all the deals within walking distance
			url = 'http://www.levr.com/phone'
			ll = str(checkin['venue']['location']['lat'])+','+str(checkin['venue']['location']['lng'])
			request_point = levr.geo_converter(ll)
			precision = 6
			results = levr_utils.get_deals_in_area(['all'],request_point,precision)

			if len(results) > 0:
				reply['text'] = "There are "+str(len(results))+" deals near you - click to view."
				reply['url'] = '' #deeplink into deal upload screen
			else:
				reply['text'] = "See any deals? Pay it forward: click to upload."
				reply['url'] = '' #deeplink into deal upload screen
		'''
		
		reply['CHECKIN_ID'] = checkin['id']
		reply['text'] = 'Hey ethan. click here to see this reply inside Levr.'
		#reply['url']  = 'fsq+unhlif5eyxsklx50dasz2pqbge2hdoik5gxbwcirc55nmq4c+reply://?contentId=abcdefg12345&fsqCallback=foursquare://checkins/'+checkin['id']
		#reply['url']  = 'fsq+unhlif5eyxsklx50dasz2pqbge2hdoik5gxbwcirc55nmq4c+reply://?contentId=abcdefg12345'
		#reply['url']  = 'http://www.levr.com?contentId=abcdefg12345'
		reply['url']  = 'http://www.levr.com/deal/blah'
		reply['contentId'] = 'abcdefg12345'
			
		url = 'https://api.foursquare.com/v2/checkins/'+reply['CHECKIN_ID']+'/reply?v=20120920&oauth_token='+'PZVIKS4EH5IFBJX1GH5TUFYAA3Z5EX55QBJOE3YDXKNVYESZ'
		#url = 'https://api.foursquare.com/v2/checkins/'+reply['CHECKIN_ID']+'/reply?v=20120920&text=hitherehello&url=foursquare%2Bunhlif5eyxsklx50dasz2pqbge2hdoik5gxbwcirc55nmq4c%2Breply%3A//%3FcontentId%3Dabcdefg12345&contentId=abcdefg12345&oauth_token='+'PZVIKS4EH5IFBJX1GH5TUFYAA3Z5EX55QBJOE3YDXKNVYESZ'
		logging.debug(url)
		#result = urlfetch.fetch(url=url,method=urlfetch.POST)
		result = urlfetch.fetch(url=url,
								payload=urllib.urlencode(reply),
								method=urlfetch.POST)
		logging.debug(levr.log_dict(result.__dict__))
		
class CatchUpHandler(webapp2.RequestHandler):
	def get(self):
		client_id = 'HD3ZXKL5LX4TFCARNIZO1EG2S5BV5UHGVDVEJ2AXB4UZHEOU'
		secret = 'LB3J4Q5VQWZPOZATSMOAEDOE5UYNL5P44YCR0FCPWFNXLR2K'
		
		#scan the database for entries with no foursquare ID
		q = levr.Business.all().filter('foursquare_id =','undefined')
		
		for business in q.run():
			ll = str(business.geo_point)
			search = urllib.quote(business.business_name)
			url = "https://api.foursquare.com/v2/venues/search?v=20120920&intent=match&ll="+ll+"&query="+search+"&client_id="+client_id+"&client_secret="+secret
			result = urlfetch.fetch(url=url)
			
			self.response.out.write('running ' + business.business_name + '\n')
			
			try:
				match = json.loads(result.content)['response']['venues'][0]
				business.foursquare_id = match['id']
				business.foursquare_name = match['name']
				business.put()
				logging.debug('added foursquare data for ' + business.business_name)
				#logging.debug(business.business_name + ' REPLACED BY ' + match['name'])
			except:
				business.foursquare_id = 'notfound'
				business.foursquare_name = 'notfound'
				business.put()
				logging.debug('no match found for ' + business.business_name)
				
		
		'''
		search = self.request.get('q')
		logging.info(search)
		url = "https://api.foursquare.com/v2/venues/search?v=20120920&intent=match&ll=42.351824,-71.11982&query="+urllib.quote(search)+"&client_id="+client_id+"&client_secret="+secret
		logging.info(url)
		result = urlfetch.fetch(url=url)
		business = json.loads(result.content)
		self.response.out.write(levr_utils.log_dict(business))
		'''

class TestHandler(webapp2.RequestHandler):
	def get(self):
		q = levr.Business.all()
		for business in q:
			business.foursquare_id = 'undefined'
			business.put()

app = webapp2.WSGIApplication([('/facebook/push', PushHandler),
								('/facebook/authorize', AuthorizeBeginHandler),
								('/facebook/authorize/exchange', ExchangeCodeHandler),
								('/facebook/authorize/complete', AuthorizeCompleteHandler),
								('/facebook/catchup', CatchUpHandler),
								('/facebook/test', TestHandler)],
								debug=True)
