from datetime import datetime
import json
import unittest
import urllib2 as u
import sys

test_url = 'http://test.levr-production.appspot.com'
fuckery_url = 'http://fuckery.levr-production.appspot.com'
live_url = 'http://www.levr.com'
local_url = 'http://0.0.0.0:8080'
base_url = test_url
# Active account info is for CarlD

active_uid = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51Ss4w7UaChA='
active_levr_token = '5VfXPghB5A90_W3pKxcaloRdnZPaSzPWXeZmUgeXDmE'
email = 'carl@levr.com'
pw = 'Carl'
alias = 'Carl'
# Test account info is for q
test_uid = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51SsytLkdChA='
test_levr_token = 'twfSOF0Xtwhx-GrrKxYVw4cLn5yEQjLTWbFvDATEDTo'

# Deal test
# deal uploaded by Bill!
deal_id = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fCHGJdErv19TaoeLGNiu51Sthw-oaChDyDrrMSui1aMhONe5YBg=='

lat = '42.365468'
lon = '-71.029486'
uid = active_uid
levr_token = active_levr_token






class TestSequence(unittest.TestCase):
	def test_search(self):
		# Test search
		endpoint = '/api/search/all'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&lat={lat}&lon={lon}'.format(uid=uid,levrToken=levr_token,lat=lat,lon=lon)
		method = 'GET'
		self._fetch(url,method,endpoint)
		
		
		
#	def test_image(self):
#		dealID = deal_id
#		endpoint = '/api/deal/{}/img'.format(dealID)
#		sizes = ['small','dealDetail']
#		method = 'GET'
#		for size in sizes:
#			url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&size={size}'.format(
#																	uid = uid,
#																	levrToken = levr_token,
#																	size= size
#																	)
#			self._fetch_img(url, method, endpoint)
	def test_deal_info(self):
		dealID = deal_id
		endpoint = '/api/deal/{}'.format(dealID)
		method = 'GET'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}'.format(uid=uid,levrToken=levr_token)
		self._fetch(url, method, endpoint)
		
#		url = base_url+endpoint
#		self._fetch(url, method, endpoint)
		
		
	def test_popular(self):
		endpoint = '/api/search/popular'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&lat={lat}&lon={lon}'.format(uid=uid,levrToken=levr_token,lat=lat,lon=lon)
		method = 'GET'
		self._fetch(url,method,endpoint)
		
	def test_login_validate(self):
		endpoint = '/api/login/validate'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}'.format(
														uid=uid,
														levrToken=levr_token)
		method = 'GET'
		self._fetch(url,method,endpoint)
	def test_login_levr(self):
		# login with email
		endpoint = '/api/login/levr'
		url = base_url+endpoint+'?email_or_owner={}&pw={}'.format(email,pw)
		method = 'GET'
		self._fetch(url,method,endpoint+' (email)')
		# login with alias
		
		endpoint = '/api/login/levr'
		url = base_url+endpoint+'?email_or_owner={}&pw={}'.format(alias,pw)
		method = 'GET'
		self._fetch(url,method,endpoint+' (owner)')
		
	
	def _fetch(self,url,method,endpoint):
		if method == 'GET':
			post_data = None
		elif method == 'POST':
			post_data = '{}'
		
		
		req = u.Request(url,post_data,{'Content-Type': 'application/json'})
		t1 = datetime.now()
		response = u.urlopen(req)
		t2 = datetime.now()
		tdiff = t2-t1
		print
		print
		print
		print base_url+endpoint+': '+str(tdiff)
		
		self.assertEqual(response.code, 200, 'Response code {} on test search'.format(response.code))
		data = json.loads(response.read())
		
#		pprint(data.get('meta',None))
		
		meta = data['meta']
		self.assertEqual(meta['success'], True, 'Call to {} returned error: "{}"'.format(url,meta.get('error','None')))
		
		return data
		
if __name__ == '__main__':
	print sys.argv
	if sys.argv.__len__() == 2:
		location = sys.argv.pop()
		if location == 'local':
			base_url = local_url
		elif location == 'test':
			base_url = test_url
		elif location == 'fuckery':
			base_url = fuckery_url
		elif location == 'live':
			base_url = live_url
		else:
			raise Exception('As a second argument pass: local, test, or live e.g. python curl_test.py test')
	
	
	print 'Running levr curl test on {}...'.format(base_url)
	
	unittest.main()
	