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
	def get(self,*args,**kwargs):
		try:
			deal = kwargs.get('deal')
			deal.been_reviewed = True
			deal.put()
			self.response.headers['Content-Type'] = 'text/plain'
			self.response.out.write('Yeah. What it do?')
			self.response.out.write(levr.log_model_props(deal, ['deal_text','deal_status','been_reviewed']))
		except Exception,e:
			levr.log_error(e)
			self.response.out.write('Error approving: '+str(e))

		
class Reject(webapp2.RequestHandler):
	@api_utils.validate('deal', None)
	def get(self,*args,**kwargs):
		try:
			deal = kwargs.get('deal')
			deal.deal_status = 'rejected'
			deal.been_reviewed = True
			deal.put()
			self.response.headers['Content-Type'] = 'text/plain'
			self.response.out.write('And the Lord said unto his children, "It has been done."\n\n')
			self.response.out.write(levr.log_model_props(deal, ['deal_text','deal_status','been_reviewed']))
		except Exception,e:
			levr.log_error(e)
			self.response.out.write('Error rejecting: '+str(e))
		
class GodLoginHandler(webapp2.RequestHandler):
	def get(self):
		'''This handler allows an admin to log in to any merchants account to manage it'''
		#grab ALLL of the business Owners, sorted alphabetically
#		owners = levr.BusinessOwner.all().order('-email').fetch(None)
#		data = []
#		for o in owners:
#			things = {
#					"email":o.email,
#					"business":o.businesses.get().business_name,
#					"id":str(o.key())
#					}
#			logging.debug(things)
#			data.append(things)
#		logging.debug(data)
#		#grab all of the businesses
#		businesses = levr.Business.all().order('-business_name').fetch(None)
#		
#		template_values = {
#						'owners':data,
#						'businesses':businesses
#						}
#		
#		template = jinja_environment.get_template('templates/god_login.html')
#		self.response.out.write(template.render(template_values))
#	def post(self):
#		logging.debug(self.request.body)
#		owner_id = self.request.get('owner_id')
#		
#		owner = levr.BusinessOwner.get(owner_id)
#		
#		session = get_current_session()
#		session['ownerID'] = enc.encrypt_key(owner_id)#business.key())
#		session['loggedIn'] = True
#		session['validated'] = owner.validated
#		self.redirect('/merchants/manage')
app = webapp2.WSGIApplication([
								('/admin/deal/(.*)/approve', Approve),
								('/admin/deal/(.*)/reject',Reject),
								],debug=True)
