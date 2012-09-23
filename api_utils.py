import json

def missing_param(param):
	return json.dumps({
		'response':{
			'meta':{
				'success':False,
				'error':'Required parameter not passed: '+param
			}
		}
	})
	
def packageUser(user,privacyLevel):
	pass
	
