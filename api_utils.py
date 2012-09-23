import json

def missing_param(self,param):
	reply = {
			'meta':{
				'success':False,
				'error':'Required parameter not passed: '+param
			},
			'alerts':{},
			'response':{}
	}
	
	self.response.out.write(json.dumps(reply))
	
def packageUser(user,privacyLevel):
	pass
	
def send_response(self,response,user=None):
	#build meta object
	meta = {'success':True,
			'error':''}
	
	#build alerts object		
	#only send back alerts with private (user-authenticated) responses (optional parameter user)
	if user != None:
		alerts = {'newNotifications':user.new_notifications}
	else:
		alerts = {'newNotifications':0}
	
	#build reply object
	reply = {'meta':meta,
				'alerts':alerts,
				'response':response}
				
	#reply
	self.response.out.write(json.dumps(reply))