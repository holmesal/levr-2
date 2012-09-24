import json
import levr_encrypt as enc
import levr_utils
import logging
from google.appengine.ext import db

def foursquare_deets(user,token):
	#goto foursquare
	url = 'https://api.foursquare.com/v2/users/self?v=20120920&oauth_token='+token
	result = urlfetch.fetch(url=url)
	foursquare_user = json.loads(result.content)['response']['user']
	#grab stuff
	user.first_name = foursquare_user['firstName']
	user.last_name = foursquare_user['lastName']
	user.photo = foursquare_user['photo']['prefix']+'500x500'+foursquare_user['photo']['suffix']
	user.email = foursquare_user['contact']['email']
	logging.info(user.__dict__)
	
	return user