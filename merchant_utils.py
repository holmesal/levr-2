from gaesessions import get_current_session
import logging
import levr_classes as levr

def login_check(self):
	'''	for merchants ONLY
		check if logged in, and return a the headerdata if so. if not, bounce to the login page'''
	session = get_current_session()
	logging.debug(session)
	if session.has_key('loggedIn') == False or session['loggedIn'] == False:
		#not logged in, bounce to login page
		logging.info('Not logged in. . .Bouncing!')
		self.redirect('/merchants/login')
		
	elif session.has_key('loggedIn') == True and session['loggedIn'] == True:
		#logged in, grab the useful bits
		#this is a hack. . . forgive meeee
		uid = session['uid']
		
		headerData = {
			'loggedIn'	: session['loggedIn'],
			'uid'		: uid,
			'owner_of'	: session['owner_of'],
			'validated'	: session['validated']
			}
		#return user metadata.
		return headerData
	return
	
def validated_check(user):
	'''checks if this user has any linked businesses or not. does not yet return these businesses'''
	
	num_bus = user.businesses.count()
	
	if num_bus > 0:
		return True
	else:
		return False
		
def create_deal(deal,business,owner):
	'''deal: a deal object
	merchant: the merchant to be set as the owner of the deal'''
	
	#init tags
	tags = []
	#add tags from the merchant
	tags.extend(business.create_tags())
	#add tags from deal stuff
	
	#create the deal
	
	
	
	
	#get businessID - not encrypted - from database
	businessID = business.key()
	logging.debug("businessID: "+str(businessID))
	
	#check if the merchant has validated their business. If so, deploy as active. If not, deploy as pending
	if validated_check(owner):
		pass