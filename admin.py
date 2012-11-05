import api_utils
import jinja2
import levr_classes as levr
import logging
import os
import webapp2
#from google.appengine.ext import db
#from google.appengine.api import images
#from gaesessions import get_current_session
#from datetime import datetime

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Approve(webapp2.RequestHandler):
	#insert into database and redirect to Pending for next pending deal
	@api_utils.validate('deal', None)
	def get(self,*args,**kwargs): #@UnusedVariable
		try:
			self.response.headers['Content-Type'] = 'text/plain'
			
			deal = kwargs.get('deal')
			deal.been_reviewed = True
			deal.put()
			
			self.response.out.write('Yeah. What it do?')
			self.response.out.write(levr.log_model_props(deal, ['deal_text','deal_status','been_reviewed']))
		except Exception,e:
			levr.log_error(e)
			self.response.out.write('Error approving: '+str(e))

		
class Reject(webapp2.RequestHandler):
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
		
app = webapp2.WSGIApplication([
								('/admin/deal/(.*)/approve', Approve),
								('/admin/deal/(.*)/reject',Reject),
								],debug=True)
