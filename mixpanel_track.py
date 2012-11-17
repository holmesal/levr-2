import base64
from google.appengine.api import urlfetch
import json
import logging

def track(event,token,properties=None):
	"""
		A simple function for asynchronously logging to the mixpanel.com API on App Engine 
		(Python) using RPC URL Fetch object.
		@param event: The overall event/category you would like to log this data under
		@param properties: A dictionary of key-value pairs that describe the event
		See http://mixpanel.com/api/ for further detail. 
		@return Instance of RPC Object
	"""
	if properties == None:
		properties = {}
	
	if token == None:
		raise Exception('mixpanel token not passed')
	
	params = {"event": event, "properties": properties}
	
	logging.info(params)
		
	data = base64.b64encode(json.dumps(params))
	request = "http://api.mixpanel.com/track/?data=" + data
	
# 	rpc = urlfetch.create_rpc()
# 	urlfetch.make_fetch_call(rpc, request)

	response = urlfetch.fetch(request)
	reply = json.loads(response.content)
	logging.info(reply)
	
# 	logging.debug(rpc)
	
	return True
	
def person(distinct_id,token,properties):
	# 
# 	if token == None:
# 		#token = "ab1137787f393161bd481e2756b77850"
# 		raise Exception('mixpanel token not passed')
		
	params = {
		"$set"		:	properties,
		"$token"	:	token,
		"$distinct_id"	:	distinct_id
	}
	
	logging.info(params)
	
	data = base64.b64encode(json.dumps(params))
	request = "http://api.mixpanel.com/engage/?data="+data
	
# 	rpc = urlfetch.create_rpc()
# 	urlfetch.make_fetch_call(rpc, request)

	response = urlfetch.fetch(request)
	reply = json.loads(response.content)
	logging.info(reply)
	
# 	logging.debug('RPC FROM MIXPANEL:')
# 	logging.debug(rpc)
	
	return True
	
def increment(distinct_id,token,to_increment):
	
	# if token == None:
# 		#token = "ab1137787f393161bd481e2756b77850"
# 		raise Exception('mixpanel token not passed')
		
	params = {
		"$add"		:	to_increment,
		"$token"	:	token,
		"$distinct_id"	:	distinct_id
	}
	
	data = base64.b64encode(json.dumps(params))
	request = "http://api.mixpanel.com/engage/?data="+data
	
# 	rpc = urlfetch.create_rpc()
# 	urlfetch.make_fetch_call(rpc, request)

	response = urlfetch.fetch(request)
	reply = json.loads(response.content)
	logging.info(reply)
	
# 	logging.debug('RPC FROM MIXPANEL:')
# 	logging.debug(rpc)
	
	return True
	

	
	