from common_word_list import blacklist
from datetime import datetime
from google.appengine.api import taskqueue
from google.appengine.ext import db
import api_utils
import geo.geohash as geohash
import json
import levr_classes as levr
import logging
import random
import webapp2
from tasks import INCREMENT_DEAL_VIEW_URL

class FindABusinessHandler (api_utils.SearchClass):
	'''
	A handler for searching for a specific venue
	'''
	api_utils.validate(None, 'param',
					user = False,
					levrToken = False,
					# fields to identify a business
					businessName = True,
					vicinity = False,
					geoPoint = False,
					radius = False,
					)
	def get(self,*args,**kwargs):
		'''
		@return: <business>
		'''
		business_name = kwargs.get('businessName')
		vicinity = kwargs.get('vicinity')
		geoPoint = kwargs.get('geoPoint')
		radius = kwargs.get('radius')
		try:
			# create a set of geo hashes to search based on the radius
			
			# If 
			
			# construct a query for each of the tokens from the business name + geohash
			
			# 
			
			pass
		except AssertionError,e:
			self.send_error(e)
		except Exception,e:
			levr.log_error()
			self.send_error()
class ViewABusinessHandler(api_utils.BaseClass):
	'''
	A handler to view the deals at a specific venue
	'''
	@api_utils.validate(None, 'param',
					user = False,
					levrToken = False,
					business = True
					)
	def get(self,*args,**kwargs):
		user = kwargs.get('actor')
		business = kwargs.get('business')
		development = kwargs.get('development',False)
		
		# set deal_status
		if development:
			deal_status = levr.DEAL_STATUS_TEST
		else:
			deal_status = levr.DEAL_STATUS_ACTIVE
		
		
		# grab all of the businesses deals
		
		deals = levr.Deal.all().filter('businessID',str(business.key())).filter('deal_status',deal_status).fetch(None)
		
		# package.
		packaged_deals = api_utils.package_deal_multi(deals, False)
		
		packaged_business = api_utils.package_business(business)
		
		# respond
		response = {
				'deals' : packaged_deals,
				'business' : packaged_business
				}
		self.send_response(response)
		

app = webapp2.WSGIApplication([
							('/api/businesses/find', FindABusinessHandler),
							('/api/businesses/view', ViewABusinessHandler),
								],debug=True)