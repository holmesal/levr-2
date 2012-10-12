from datetime import datetime,timedelta
from google.appengine.ext import db
from math import floor
import api_utils
import api_utils_social as social
import levr_classes as levr
import levr_encrypt as enc
import logging
import random
import webapp2


class LoginFacebookHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=True,remoteToken=False)
	def get(self,*args,**kwargs):
		#=======================================================================
		# This is not finished. Do not use.
		#=======================================================================
		#RESTRICTED
		try:
			token 		= kwargs.get('remoteToken')
			facebook_id = int(kwargs.get('remoteID'))
			
			user = levr.Customer.all().filter('facebook_id',facebook_id).get()
			assert user, 'Facebook user is not registered with Levr, remoteID: {}'.format(facebook_id)
			
			#TODO: update users facebook info
			
			response = {
					'user':api_utils.package_user(user,True,send_token=True)
					}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class LoginFoursquareHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=False,remoteToken=True)
	def get(self,*args,**kwargs):
		try:
			#===================================================================
			# This is not finished. Do not use.
			#===================================================================
			
			#RESTRICTED
			logging.debug('LOGIN FOURSQUARE\n\n\n')
			logging.debug(kwargs)
			
			#check token
			foursquare_id	= kwargs.get('remoteID',None)
			foursquare_token= kwargs.get('remoteToken',None)
			
			#find user with matching credentials
			if foursquare_id:
				user = levr.Customer.all().filter('foursquare_id',foursquare_id).get()
			else:
				#
				user = levr.Customer.all().filter('foursquare_token',foursquare_token).get()
			
			#if user could not be found, their foursquare_token might have changed
			#consult foursquare
			if not user:
				### HACKY WORKAROUND
				#spoof user object
				user = levr.Customer()
				user = social.Foursquare(user)
				#add foursquare credentials
				user.foursquare_id = foursquare_id
				user.foursquare_token = foursquare_token
				
				try:
					#connect to foursquare, and grab new info
					new_user_details = user.update_user_details()
				except Exception,e:
					#could not connect to foursquare
					assert False, 'Foursquare user is not registered with Levr: {}'.format(e)
				### /HACKY WORKAROUND
			
			response = {
					'user':api_utils.package_user(existing_user,True,send_token=True)
					}
			api_utils.send_response(self,response,existing_user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
			
class LoginTwitterHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,remoteID=True,remoteToken=True,remoteTokenSecret=True)
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('LOGIN TWITTER\n\n\n')
			logging.debug(kwargs)
			#check token
			twitter_id				= int(kwargs.get('remoteID'))
			twitter_token			= kwargs.get('remoteToken')
			twitter_token_secret	= kwargs.get('remoteTokenSecret')
			#check token
			
			#find the user with the specified twitter_id
			user = levr.Customer.all().filter('twitter_id',twitter_id).get()
			
			#assure that a user exists with this twitter id
			assert user, 'Twitter user is not registered with Levr, remoteID: {}'.format(twitter_id)
			logging.debug(user.twitter_token_secret != twitter_token_secret)
			logging.debug(user.twitter_token != twitter_token)
			#authenticate user from the server and update info
			if user.twitter_token != twitter_token or user.twitter_token_secret != twitter_token_secret:
				#the users auth token does not match, but may have changed. check with twitter.
				logging.debug('{} != {}'.format(user.twitter_token,twitter_token))
				logging.debug('{} != {}'.format(user.twitter_token_secret,twitter_token_secret))
				user = social.Twitter(user)
				
				try:
					logging.debug('eee')
					new_user, new_user_details, new_friends = user.first_time_connect(
																				
																				twitter_id = twitter_id,
																				twitter_token = twitter_token,
																				twitter_token_secret = twitter_token_secret
																				)
					logging.debug('eee')
				except Exception,e:
					#failed authentication
					#TODO: when error handling on the remote responses is improved, this will change
					assert False, 'User could not be authenticated with Twitter. '.format(e)
				else:
					response = {
							'user'				: api_utils.package_user(new_user,True,send_token=True),
							}
			else:
				logging.debug('{} == {}'.format(user.twitter_token,twitter_token))
				logging.debug('{} == {}'.format(user.twitter_token_secret,twitter_token_secret))
				logging.debug('THEY ARE EQUAL')
				#credentials are matched. 
				#TODO: run task to update users information
				#return the user
				response = {
						'user':api_utils.package_user(user,True,send_token=True)
						}
			api_utils.send_response(self,response,user)
		except AssertionError,e:
			levr.log_error()
			api_utils.send_error(self,'{}'.format(e))
		except Exception,e:
			levr.log_error()
			api_utils.send_error(self,'Server Error {}'.format(e))
			
			
class LoginLevrHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,email_or_owner=True,pw=True)
	def get(self,*args,**kwargs):
		try:
			#RESTRICTED
			logging.debug('LOGIN LEVR\n\n\n')
			logging.debug(kwargs)
			
			email_or_owner = kwargs.get('email_or_owner')
			pw = kwargs.get('pw')
			
			#check both email and password
			pw = enc.encrypt_password(pw)
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
			#grabthe user from the input
			user = kwargs.get('actor')
			
			response = {'user':api_utils.package_user(user,True)}
			
			data = SpoofUndeadNinjaActivity(user,True).run()
			logging.debug(levr.log_dict(data))
			#set last login
			user = data['user']
#			user.date_last_login = datetime.now() - timedelta(days=1)
#			logging.debug(user.date_last_login)
			user.put()
			api_utils.send_response(self,response,user)
			
			
		except:
			levr.log_error()
			api_utils.send_error(self,'Server Error')
class Test(webapp2.RequestHandler):
	def get(self):
		user = levr.Customer.all().filter('email','ethan@levr.com').get()
		
		output = SpoofUndeadNinjaActivity(user,True).run()
		api_utils.send_response(self,output)
		
class SpoofUndeadNinjaActivity:
	'''
	The undead walk the earth! And they like things!
	'''
	def __init__(self,user,development=False,**kwargs):
		self.user = user
		self.development = development
		self.now = datetime.now()
		self.now_in_seconds = long(levr.unix_time(self.now))
		#set development params
		if self.development:
			deal_status = 'test'
		else:
			deal_status = 'active'
		
		#fetch all of the users active deals
		self.user_deals				= levr.Deal.all().ancestor(self.user.key()).filter('deal_status', deal_status).fetch(None)
		logging.debug(self.user_deals)
		#calculate the date since last upload
		logging.debug(self.user.date_last_login)
		logging.debug(type(self.user.date_last_login))
		self.days_since_last_login = self.calc_days_since(self.user.date_last_login)
		logging.debug(self.days_since_last_login)
		logging.debug(type(self.days_since_last_login))
		
		#set environment params
		self.max_likes_per_day		= kwargs.get('max_likes_per_day',3) #a.k.a. the number of chances to like in a day
		
		self.ideal_likes_per_day	= float(kwargs.get('ideal_likes_per_day',2))
		
		#constrain system...
		assert type(self.max_likes_per_day) == int, 'max likes per day must be int'
		assert type(self.ideal_likes_per_day) == float or type(self.ideal_likes_per_day) == int , 'ideal_likes_per_day must be float or int'
		assert self.max_likes_per_day > self.ideal_likes_per_day , 'Max likes per day must be greater than the ideal'
		
		#set the chance that the deal will be liked per iteration
		self.chance_of_like = self.ideal_likes_per_day / self.max_likes_per_day
		
		
	def run(self):
		'''
		WARNING: DOES NOT REPLACE THE USER WHEN RETURNING
		'''
		#the users accumulated notifications
		notifications = []
		#the accumulated undead ninjas
		undead_ninjas_set = set()
		for deal in self.user_deals:
#			days_since_upload = self.calc_days_since(deal.date_created)
#			logging.debug(days_since_upload)
			whole_days = int(floor(self.days_since_last_login))
			partial_days = self.days_since_last_login - whole_days
			
			#add up likes for whole days
			total_likes = 0
			for day in range(0,whole_days):
				total_likes += self.get_likes_per_day(self.chance_of_like, self.max_likes_per_day)
			
			#add up likes from the partial day
			total_likes += self.get_likes_per_day(self.chance_of_like, self.max_likes_per_day) * partial_days
			
			
#			likes_per_day	= self.get_likes_per_day(self.chance_of_like, self.max_likes_per_day)
#			logging.debug('likes per day: '+str(likes_per_day))
#			logging.debug('total days: '+str(self.days_since_last_login))
#			total_likes		= likes_per_day * self.days_since_last_login
			logging.debug('total likes: '+str(total_likes))
			#round off total likes to an integer
			total_likes		= floor(total_likes)
			logging.debug('total likes: '+str(total_likes))
			
			
			#fetch the appropriate number of ninjas
			undead_ninjas = api_utils.get_random_dead_ninja(total_likes)
			logging.debug(undead_ninjas)
			#make sure undead_ninjas is a list
			if type(undead_ninjas) != list:
				undead_ninjas = [undead_ninjas]
			#add these undead ninjas to the list of undead ninjas that are being updated
			
			
			#The decided number of ninjas will like the deal
			for ninja in undead_ninjas:
				#only add the 
				if deal.key() not in ninja.upvotes:
					#increase the deals upvotes
					deal.upvotes += 1
					#log that the undead ninja has liked this deal
					ninja.upvotes.append(deal.key())
					#increase the users karma
					self.user.karma += 1
					#update notification count
					self.user.new_notifications += 1
					#===========================================================
					# Remember to change this if the create notifications functionality changed
					#===========================================================
					#create the notification
					notifications.append(levr.Notification(
										notification_type	= 'upvote',
										line2				= random.choice(levr.upvote_phrases),
										to_be_notified		= [self.user.key()],
										actor				= ninja.key(),
										deal				= deal.key(), #default to None,
										date_in_seconds		= self.now_in_seconds
										))
				else:
					assert False
			undead_ninjas_set.update(undead_ninjas)
					
					
		
		#update the users level
		api_utils.level_check(self.user)
		
		db.put(notifications)
#		db.put(self.user)
		db.put(undead_ninjas_set)
		
		return {
			'notifications':str(notifications),
			'user':self.user,
			'undead_ninjas':str(undead_ninjas_set)
			}
	def get_likes_per_day(self,chance_to_like,max_likes):
		'''
		Generates the number of likes per day the deal will get based on the chance that the deal will be liked in a day and the max number of likes in a day
		
		@param chance_to_like: The chance that the deal will be liked per simulation
		@type chance_to_like: float 0-1
		@param max_likes: The number of times the simulation will be run
		@type max_likes: int
		'''
		likes = 0
		for i in range(0,max_likes):
			num = random.uniform(0,1)
			if num <= chance_to_like:
				likes += 1
		return likes
		
		
	
	
	def calc_days_since(self,date):
		diff = self.now - date
		logging.debug(self.now)
		logging.debug(date)
		logging.debug(type(date))
		logging.debug(diff)
		logging.debug(type(diff))
		logging.debug(diff.total_seconds)
		seconds_since = self.now_in_seconds - levr.unix_time(date)
		logging.debug(seconds_since)
		days_since = seconds_since/60./60./24.
		logging.debug('days since: '+str(days_since))
		return days_since
	
		
		
		
	
	
	
	
app = webapp2.WSGIApplication([('/api/login/facebook', LoginFacebookHandler),
								('/api/login/foursquare', LoginFoursquareHandler),
								('/api/login/twitter', LoginTwitterHandler),
								('/api/login/levr', LoginLevrHandler),
								('/api/login/validate', LoginValidateHandler),
								('/api/login/test', Test)
								],debug=True)