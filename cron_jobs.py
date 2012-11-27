from datetime import datetime
from google.appengine.ext import db, deferred
import api_utils
import levr_classes as levr
import logging
import webapp2
#import json
#import levr_encrypt as enc
#import random

class ExpireDealsHandler(webapp2.RequestHandler):
	'''
	A cron job to expire deals that are more than 7 days old
	'''
	def get(self):
		try:
			now = datetime.now()
			#fetch all deals that are set to expire
			deals = levr.Deal.all().filter('deal_status','active').filter('date_end <=',now).filter('date_end !=',None).fetch(None)
			logging.info('<-- With date_end -->\n\n')
			for deal in deals:
				logging.info(str(deal.date_end)+' --> '+ deal.deal_text+'\n')
				
			
			### DEBUG ###
			# This is the control group of all active deals
			logging.info('\n\n<-- Without date end -->\n\n')
			deals2 = levr.Deal.all().filter('deal_status','active').fetch(None)
			for deal in deals2:
				logging.info(str(deal.date_end)+' --> '+ deal.deal_text+ '\n')
			## /DEBUG ###
			
			
#			#set deal_status to expired
#			for deal in deals:
#				# expire the deal
#				deal.expire()
			
			deals = [deal.expire for deal in deals]
			# TODO: test this
			#replace deals
			db.put(deals)
			
		except:
			levr.log_error()

app = webapp2.WSGIApplication([
							('/cronjobs/expireDeals', ExpireDealsHandler)
								],debug=True)