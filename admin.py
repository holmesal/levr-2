import api_utils
import jinja2
import levr_classes as levr
import logging
import os
import webapp2
from datetime import datetime,timedelta
from google.appengine.ext import db
import levr_encrypt as enc
#from google.appengine.api import images
#from gaesessions import get_current_session
#from datetime import datetime

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
categories = [
'Food',
'Breakfast',
'Lunch',
'Dinner',
'Takeout',

'Drink',
'Beer',
'Wine',

'Restaurant',
'Bar',
'Diner',
'Cafe',
'Pub',

]

class ReviewHandler(api_utils.BaseClass):
	@api_utils.validate('deal', None)
	def get(self,*args,**kwargs):
		try:
			deal = kwargs.get('deal')
			deal = levr.Deal.all().filter('been_reviewed',False).get()
			assert deal.been_reviewed == False, 'Es tut mir wirklich leid. Der Deal bereits ueberprueft.'
			
			template_values = {
							'categories' : categories,
							'deal' : deal,
							'small_img'		: api_utils.create_img_url(deal,'small'),
							'post_url' : '/admin/deal/{}/review'.format(enc.encrypt_key(deal.key()))
							}
			
			template = jinja_environment.get_template('templates/admin/categorize.html')
			self.response.out.write(template.render(template_values))
		except AssertionError,e:
			self.response.out.write(str(e))
		except:
			self.send_fail()
	@api_utils.validate('deal', None)
	def post(self,*args,**kwargs):
		deal = kwargs.get('deal')
		days = self.request.get('days_to_expire')
		tags = self.request.get('categories',allow_multiple=True)
		try:
			days = int(days)
			#===================================================================
			# Register categorization
			#===================================================================
			api_utils.KWLinker.register_categorization(deal, tags, stemmed=False)
			#===================================================================
			# Set the deal expiration
			#===================================================================
			
			self.response.headers['Content-Type'] = 'text/plain'
			assert deal.been_reviewed == False, 'Es tut mir wirklich leid. Der Deal bereits ueberprueft.'
			
			if days < 0:
				date_end = None
				days = None
			else:
				date_end = deal.date_created + timedelta(days=days)
			
			deal.date_end = date_end
			
			#===================================================================
			# Add the new keywords to the deals set of tags
			#===================================================================
			deal.extra_tags = list(set(deal.extra_tags.extend(tags)))
			
			#===================================================================
			# Finalize deal
			#===================================================================
			deal.been_reviewed = True
			deal.put()
			
			self.response.out.write(levr.log_model_props(deal))
			
			if days == None:
				self.response.out.write('Success! This deal will not expire')
			else:
				self.response.out.write('Success! The deal is set to expire in {} days\n'.format(days))
				self.response.out.write('created: {}\nexpire:  {}'.format(deal.date_created,date_end))
			
		except AssertionError,e:
			self.response.out.write(e)
		except Exception,e:
			levr.log_error()
			self.response.out.write('Error rejecting: '+str(e))
		pass
		
class RejectHandler(api_utils.BaseClass):
	@api_utils.validate('deal', None)
	def get(self,*args,**kwargs): #@UnusedVariable
		try:
			self.response.headers['Content-Type'] = 'text/plain'
			deal = kwargs.get('deal')
			assert deal.been_reviewed == False, 'Deal has already been reviewed.'
			# remove the deal from the memcache
			try:
				levr.remove_memcache_key_by_deal(deal)
			except:
				levr.log_error('Could not remove key from memcache')
			deal.deal_status = 'rejected'
			deal.been_reviewed = True
			deal.put()
			
			self.response.out.write('And the Lord said unto his children, "It has been done."\n\n')
			self.response.out.write(levr.log_model_props(deal, ['deal_text','deal_status','been_reviewed']))
		except AssertionError,e:
			self.response.out.write(e)
		except Exception,e:
			levr.log_error(e)
			self.response.out.write('Error rejecting: '+str(e))
class SetExpirationHandler(api_utils.BaseClass):
	@api_utils.validate('deal',None,daysToExpire=True)
	def get(self,*args,**kwargs): #@UnusedVariable
		'''
		Sets the expiration date for a deal.
		tAvkZDR8iEAh2w29fBwSmL9j8cmANDORXoQAH1a5dGL9nMvplJapOBWmpQZRtsQIfzbEELvxUcG-eOl_OP4KPEOI4Q==
		@param daysToExpire: number of days this deal is live
		'''
		deal = kwargs.get('deal')
		days = kwargs.get('daysToExpire')
		try:
			self.response.headers['Content-Type'] = 'text/plain'
			assert deal.been_reviewed == False, 'Es tut mir wirklich leid. Der Deal bereits ueberprueft.'
			
			if days < 0:
				date_end = None
				days = None
			else:
				date_end = deal.date_created + timedelta(days=days)
			
			deal.date_end = date_end
#			deal.been_reviewed = True
			deal.put()
			
			if days == None:
				self.response.out.write('Success! This deal will not expire')
			else:
				self.response.out.write('Success! The deal is set to expire in {} days\n'.format(days))
				self.response.out.write('created: {}\nexpire:  {}'.format(deal.date_created,date_end))
			
		except AssertionError,e:
			self.response.out.write(e)
		except Exception,e:
			levr.log_error()
			self.response.out.write('Error rejecting: '+str(e))

class ReanimateHandler(api_utils.BaseClass):
	@api_utils.validate('deal',None)
	def get(self,*args,**kwargs):
	
		deal = kwargs.get('deal')
		
		try:
			deal.deal_status = 'active'
			deal.put()
			
			
			
		except AssertionError,e:
			self.response.out.write(e)
		except Exception,e:
			levr.log_error()
			
class DashboardHandler(webapp2.RequestHandler):
		def get(self):
			
			geo_hash_set = ['drt3','drmr','drt8','drt0','drt1','drt9','drmx','drmp','drt2']
			
			active_dict = api_utils.get_deal_keys_from_db(geo_hash_set,'active',None)
			active_keys = []
			for active in active_dict:
				active_keys.extend(active_dict[active])
				
			expired_dict = api_utils.get_deal_keys_from_db(geo_hash_set,'expired',None)
			expired_keys = []
			for expired in expired_dict:
				expired_keys.extend(expired_dict[expired])
				
			rejected_dict = api_utils.get_deal_keys_from_db(geo_hash_set,'rejected',None)
			rejected_keys = []
			for rejected in rejected_dict:
				rejected_keys.extend(rejected_dict[rejected])
			
			deals = db.get(active_keys+expired_keys+rejected_keys)
			
			packaged_deals = api_utils.package_deal_multi(deals)
			
# 			logging.info(packaged_deals)
			

			
			active_deals = []
			expired_deals = []
			rejected_deals = []
			
			
			for deal in packaged_deals:
				
				deal['lat'] = deal['business']['geoPoint'].split(',')[0]
				deal['lon'] = deal['business']['geoPoint'].split(',')[1]
				#fix image url
				deal['imgURL'] = deal['largeImg'].split('?')[0]+'?size=webMapView'
				#links
				
				
# 				logging.info(deal['origin'])
				if deal['origin'] != 'foursquare':
					if deal['origin'] == 'levr':
						deal['pin_style'] = 'star'
					elif deal['origin'] == 'merchant':
						deal['pin_style'] = 'dot'
					else:
						deal['pin_style'] = 'question-mark'
					
	# 				logging.info(deal['status'])
					if deal['status'] == 'active':
						deal['pin_color'] = '60b03c'
						active_deals.append(deal)
					elif deal['status'] == 'expired':
						deal['pin_color'] = 'dfb72a'
						expired_deals.append(deal)
					elif deal['status'] == 'rejected':
						deal['pin_color'] = 'df2a2a'
						rejected_deals.append(deal)
				
				
				
				
			template_values = {
				"active_deals"		:	active_deals,
				"expired_deals"		:	expired_deals,
				"rejected_deals"	:	rejected_deals
			}
			
# 			logging.info(template_values)
			
			#launch the jinja environment
			jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
			template = jinja_environment.get_template('templates/dashboard.html')
			self.response.out.write(template.render(template_values))
		

app = webapp2.WSGIApplication([
								('/admin/deal/(.*)/review', ReviewHandler),
								('/admin/deal/(.*)/reject',RejectHandler),
								('/admin/deal/(.*)/reanimate',ReanimateHandler),
								('/admin/deal/(.*)/expiration',SetExpirationHandler),
								('/admin/dashboard',DashboardHandler)
								],debug=True)
