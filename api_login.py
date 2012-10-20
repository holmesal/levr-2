from datetime import datetime
import api_utils
import levr_classes as levr
import levr_encrypt as enc
import logging
import webapp2

			
class LoginLevrHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,email_or_owner=True,pw=True)
	def get(self,*args,**kwargs):
		'''
		A user logs in with levr using an email or alias, and a password
		'''
		try:
			#RESTRICTED
			logging.debug('LOGIN LEVR\n\n\n')
			logging.debug(kwargs)
			
			email_or_owner = kwargs.get('email_or_owner')
			pw = kwargs.get('pw')
			pw = enc.encrypt_password(pw)
			
			
			#check both email and password
			
			r_email = levr.Customer.gql('WHERE email = :1 AND pw=:2',email_or_owner,pw).get()
			r_alias  = levr.Customer.gql('WHERE alias = :1 AND pw=:2',email_or_owner,pw).get()
			if r_email:
				#match based on email
				existing_user = r_email
			elif r_alias:
				#match based on alias
				existing_user = r_alias
			else:
				api_utils.send_error(self,'Authentication failed.')
				return
			
			#create or refresh the alias
			existing_user = levr.build_display_name(existing_user)
			
			#===================================================================
			# Spoof Ninja Activity!
			#===================================================================
			
			data = api_utils.SpoofUndeadNinjaActivity(existing_user).run()
			logging.debug(levr.log_dict(data))
			#set last login
			existing_user = data['user']
			#still here? update last login by putting
			existing_user.put()
			
			#package user, private setting, send token
			response = {'user':api_utils.package_user(existing_user,True,send_token=True)}
			
			api_utils.send_response(self,response,existing_user)
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class LoginValidateHandler(webapp2.RequestHandler):
	@api_utils.validate(None,'param',user=True,levrToken=True)
	@api_utils.private
	def get(self,*args,**kwargs):
		try:
			logging.info('Reporting for dudty, Captain')
			#grabthe user from the input
			user = kwargs.get('actor')
			
			
			
			try:
				data = api_utils.SpoofUndeadNinjaActivity(user).run()
				logging.debug(levr.log_dict(data))
				#set last login
				user = data['user']
			except:
				levr.log_error()
				
			user.date_last_login = datetime.now()
#			logging.debug(user.date_last_login)
			user.put()
			response = {'user':api_utils.package_user(user,True)}
			api_utils.send_response(self,response,user)
			
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
		
		
		
		
	
	
	
	
app = webapp2.WSGIApplication([
#								('/api/login/facebook', LoginFacebookHandler),
#								('/api/login/foursquare', LoginFoursquareHandler),
#								('/api/login/twitter', LoginTwitterHandler),
								('/api/login/levr', LoginLevrHandler),
								('/api/login/validate', LoginValidateHandler),
								],debug=True)