from google.appengine.api import urlfetch
import api_utils
import api_utils_social as social
import jinja2
import json
import levr_classes as levr
import logging
import os
import urllib
import webapp2
import mixpanel_track as mp_track
import time
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
		logging.debug('Hit the Authorize Begin Handler')
		client_id = 'UNHLIF5EYXSKLX50DASZ2PQBGE2HDOIK5GXBWCIRC55NMQ4C'
		redirect = 'https://levr-production.appspot.com/foursquare/authorize/complete'
		url = "https://foursquare.com/oauth2/authenticate?client_id="+client_id+"&response_type=code&redirect_uri="+redirect
		self.redirect(url)
		
class AuthorizeCompleteHandler(webapp2.RequestHandler):
	def get(self):
		try:
			logging.debug('Hit the Authorize Complete Handler')
			client_id = 'UNHLIF5EYXSKLX50DASZ2PQBGE2HDOIK5GXBWCIRC55NMQ4C'
			secret = 'VLKDNIT0XSA5FK3XIO05DAWVDVOXTSUHPE4H4WOHNIZV14G3'
			redirect = 'https://levr-production.appspot.com/foursquare/authorize/complete'
			code = self.request.get('code')
			
			#make request for token
			url = "https://foursquare.com/oauth2/access_token?client_id="+client_id+"&client_secret="+secret+"&grant_type=authorization_code&redirect_uri="+redirect+"&code="+code
			result = urlfetch.fetch(url=url)
			token = json.loads(result.content)['access_token']
			logging.info(token)
			
			#grab more user details
			url = 'https://api.foursquare.com/v2/users/self?v=20120920&oauth_token='+token
			result = urlfetch.fetch(url=url)
			response_dict = json.loads(result.content)
			
			logging.debug(levr.log_dict(response_dict))
			
			#let the foursquare parsing code do its thing
			user = social.Foursquare(foursquare_token=token)
			
			user,new_details,new_friends = user.connect_with_content(response_dict,True,foursquare_token=token)
			
			logging.debug(levr.log_model_props(user))
			logging.debug(levr.log_dict(new_details))
			logging.debug(levr.log_dict(new_friends))
			
			
			#send the founders a text
			levr.text_notify(user.first_name + ' ' + user.last_name + ' from foursquare')
			
			#launch the jinja environment
			jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
			#set up the jinja template and echo out
			template = jinja_environment.get_template('templates/landing.html')
			self.response.out.write(template.render())
			
			logging.debug(levr.log_dict(user))
		except:
			levr.log_error()
			self.response.out.write('Could not connect with Foursquare')

class PushHandler(webapp2.RequestHandler):
	'''
	What does this do?
	'''
	def post(self):
		try:
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
			user = levr.Customer.gql('WHERE foursquare_id = :1',int(checkin['user']['id'])).get()
			
			#initialize the response object - these are defaults
			contentID = levr.create_content_id('foursquare')
			levr_url = 'http://www.levr.com/mobile/'+contentID
			
			#search for expired offers at that business
			#q_expired = levr.Deal.gql('WHERE businessID=:1 AND deal_status=:2',business)
			
			if business:	#business found - CURRENTLY ONLY REPLYING AT BUSINESSES THAT ARE IN OUR DATABASE
				#for deal in levr.Deal().all().filter('businessID =', str(business.key())).run():
				q = levr.Deal.gql("WHERE businessID = :1 AND deal_status = :2 ORDER BY count_redeemed DESC",str(business.key()),'active')
				
				deal = None
				
				for d in q:
					if d.origin != 'foursquare':
						deal = d
						text = 'Click to view the most popular offer here: '+ deal.deal_text
						action='deal'
						break
				else:
					text = "See any deals? Pay it forward! Click to add."
					action = 'upload'
					deal = None
	
	#	
	# 			
	# 			numdeals = q.count()
	# 			if numdeals > 0:	#many deals found
	# 				deal_matched = False
	# 				text = "See any deals? Pay it forward! Click to add."
	# 				action = 'upload'
	# 				while deal_matched == False:
	# 					deal = q.get()
	# 					if deal.origin != 'foursquare':
	# 						text = 'Click to view the most popular offer here: '+ deal.deal_text
	# 						action='deal'
	# 						deal_matched = True
	# 			else:	#no deals found
	# 				text = "See any deals? Pay it forward! Click to add."
	# 				action = 'upload'
			
				#create floating_content entity and put
				floating_content = levr.FloatingContent(
					action=action,
					origin='foursquare',
					contentID=contentID,
					user=user,
					deal=deal,
					business=business
				)
				floating_content.put()
				
				#track event via mixpanel (asynchronous)
				properties = {
					'time'				:	time.time(),
					'distinct_id'		:	str(user.key()),		#not encrypted
					'mp_name_tag'		:	user.display_name
				}
				mp_track.track('Foursquare checkin reply',properties)
				
				
				reply = {
					'CHECKIN_ID'		:checkin['id'],
					'text'				:text,
					'url'				:levr_url,
					'contentId'			:contentID
				}
			
			
			
				'''else:			#no business found
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
						reply['url'] = '' #deeplink into deal upload screen'''
						
				
				#reply['CHECKIN_ID'] = checkin['id']
				#reply['text'] = 'Hey ethan. click here to see this reply inside Levr.'
				#reply['url']  = 'fsq+unhlif5eyxsklx50dasz2pqbge2hdoik5gxbwcirc55nmq4c+reply://?contentId=abcdefg12345&fsqCallback=foursquare://checkins/'+checkin['id']
				#reply['url']  = 'fsq+unhlif5eyxsklx50dasz2pqbge2hdoik5gxbwcirc55nmq4c+reply://?contentId=abcdefg12345'
				#reply['url']  = 'http://www.levr.com?contentId=abcdefg12345'
				#reply['url']  = 'http://www.levr.com/deal/blah'
				#reply['contentId'] = 'abcdefg12345'
					
				url = 'https://api.foursquare.com/v2/checkins/'+checkin['id']+'/reply?v=20120920&oauth_token='+user.foursquare_token
				#url = 'https://api.foursquare.com/v2/checkins/'+reply['CHECKIN_ID']+'/reply?v=20120920&text=hitherehello&url=foursquare%2Bunhlif5eyxsklx50dasz2pqbge2hdoik5gxbwcirc55nmq4c%2Breply%3A//%3FcontentId%3Dabcdefg12345&contentId=abcdefg12345&oauth_token='+'PZVIKS4EH5IFBJX1GH5TUFYAA3Z5EX55QBJOE3YDXKNVYESZ'
				logging.debug(url)
				#result = urlfetch.fetch(url=url,method=urlfetch.POST)
				result = urlfetch.fetch(url=url,
										payload=urllib.urlencode(reply),
										method=urlfetch.POST)
				logging.debug(levr.log_dict(result.__dict__))
			else:
				logging.info('BUSINESS NOT FOUND')
		except:
			levr.log_error()
			self.reponse.out.write('Could not connect with Foursquare')
		
class CatchUpHandler(webapp2.RequestHandler):
	'''
	What does this do?
	'''
	def get(self):
		try:
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
		except:
			levr.log_error()
			self.response.out.write('Could not connect with Foursquare')

class TestHandler(webapp2.RequestHandler):
	def get(self):
		q = levr.Business.all()
		for business in q:
			business.foursquare_id = 'undefined'
			business.put()

app = webapp2.WSGIApplication([('/foursquare/push', PushHandler),
								('/foursquare/authorize', AuthorizeBeginHandler),
								('/foursquare/authorize/complete', AuthorizeCompleteHandler),
								('/foursquare/catchup', CatchUpHandler),
								('/foursquare/test', TestHandler)],
								debug=True)
