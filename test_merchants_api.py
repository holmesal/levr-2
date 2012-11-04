from datetime import datetime
from pprint import pprint
import json
import unittest
import urllib2 as u
import promotions as promo
test_url = 'http://test.latest.levr-production.appspot.com'
live_url = 'http://www.levr.com'
local_url = 'http://0.0.0.0:8080'
base_url = test_url

lat = '42.365468'
lon = '-71.029486'


# Active account info is for CarlD

#active_uid = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51Ss4w7UaChA='
#active_levr_token = '5VfXPghB5A90_W3pKxcaloRdnZPaSzPWXeZmUgeXDmE'
#email = 'carl@levr.com'
#pw = 'Carl'
#alias = 'Carl'
# Test account info is for q
test_uid 			= 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51StjnMAaChA='
test_levr_token 	= '4QeGPF4WtlUlpG7pKxAXl90LyZGBFT6ECLdvCwPJXDI'
test_business_name 	= 'Ali_Gs_House_of_wonderss1'
test_vicinity 		= '260_Everett_St'
test_geo_point 		= '{},{}'.format(lat,lon)
test_types 			= 'one,two,three,apple_tree!,legal'
test_pw 			= 'carl1'
test_email 			= 'merchtest1@levr.com'
test_business_id 	= 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErvitTapPLKLhLS0Ss_1-IaChA='
# Deal test

test_deal_id = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fC3GJdErv19TaoeLGNiu51StjnMAaChDyDrrMSui1aMhOG-0X'
# deal uploaded by Bill!
#deal_id = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fCHGJdErv19TaoeLGNiu51Sthw-oaChDyDrrMSui1aMhONe5YBg=='


#uid = test_uid
#levr_token = test_levr_token
business_name = test_business_name
vicinity = test_vicinity
geo_point = test_geo_point
types = test_types
pw = test_pw
email = test_email
development = True
#deal = None
#deal_id = test_deal_id
#businessID = test_business_id

refresh = True

class TestSequence(unittest.TestCase):
	def test_connect(self):
		endpoint = '/api/merchant/connect'
		url = base_url+endpoint+'?email={email}&pw={pw}&businessName={businessName}&vicinity={vicinity}&ll={ll}&types={types}&development={development}'.format(
						email = email,
						pw = pw,
						businessName = business_name,
						vicinity = vicinity,
						ll = geo_point,
						types = types,
						development = development
				)
		method = 'POST'
		data = self._fetch(url, method, endpoint)
		user = data['response']['user']
		business = data['response']['business']
		
		self.business_name = business.get('businessName',None)
		self.vicinity = business.get('vicinity',None)
		self.geo_point = business.get('geoPoint',None)
		
		self.assertEqual(self.business_name, business_name, 'business_name: {} != {}'.format(self.business_name,business_name))
		self.assertEqual(self.vicinity, vicinity, 'vicinity: {} != {}'.format(self.vicinity,vicinity))
		self.assertEqual(self.geo_point,geo_point,'geo_point: {} != {}'.format(self.geo_point,geo_point))
		# store data for later use
		self.businessID = business.get('businessID',None)
		
		uid = user.get('uid',None)
		levr_token = user.get('levrToken',None)
		
#		self.assertEqual(uid,remote_uid, 'Uid does not match...')
#		self.assertEqual(levr_token,remote_levr_token, 'token does not match...')
		assert uid, 'No uid, cannot continue'
		assert levr_token, 'No levr_token, cannot continue'
		
		print '--> uid: ',uid
		print '--> levr_token: ',levr_token
		
#	def test_request_upload(self):
		#=======================================================================
		# Request uploads
		#=======================================================================
		endpoint = '/api/merchant/upload/request'
		actions = ['add','edit']
		method = 'GET'
		for action in actions:
			url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&action={action}'.format(uid=uid,
																						levrToken=levr_token,
																						action=action
																						)
			data = self._fetch(url, method, endpoint)
			print '--> upload url: ',data['response']['uploadURL']
			
#	def test_get_merchant_deals(self):
		#=======================================================================
		# Get Deals
		#=======================================================================
		endpoint = '/api/merchant/deals'
		method = 'GET'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}'.format(uid=uid,
																		levrToken = levr_token)
		
		data = self._fetch(url, method, endpoint)
		deals = data['response'].get('deals',[])
		self.assertEqual(type(deals),list,'Deals is not list: {}'.format(type(deals)))
		self.assertGreater(deals.__len__(), 0, 'empty deals!')
		print '--> deals: ', deals.__len__()
		
		deal = deals[0]
		deal_id = deal.get('dealID','')
		print '--> deal_id: ', deal_id
		assert deal_id, 'No deal.. Cannot continue'
		pre_promotion_karma = deal.get('karma',-1)
	
#	def test_expire_deal(self):
		#=======================================================================
		# Expire Deal
		#=======================================================================
		endpoint = '/api/merchant/remove'
		method = 'POST'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&dealID={dealID}'.format(uid=uid,
																						levrToken=levr_token,
																						dealID = deal_id
																						)
		data = self._fetch(url, method, endpoint)
		status = data['response']['deal']['status']
		print '--> status: ',status
		self.assertEqual(status, 'expired', 'Invalid deal status: {} != {}'.format(status,'expired'))
		
#	def test_reactivate_deal(self):
		#=======================================================================
		# Reactivate Deal
		#=======================================================================
		endpoint = '/api/merchant/reactivate'
		method = 'POST'
		url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&dealID={dealID}'.format(uid=uid,
																		levrToken=levr_token,
																		dealID = deal_id
																		)
		data = self._fetch(url, method, endpoint)
		status = data['response']['deal']['status']
		print '--> status: ', status
		self.assertEqual(status, 'test', 'Invalid deal status: {} != {}'.format(status,'test'))
		
		
		#=======================================================================
		# Fetch promotions
		#=======================================================================
		endpoint = '/api/merchant/promote/get'
		method = 'GET'
		url = base_url+endpoint
		
		data = self._fetch(url, method, endpoint)
		remote_promos = data['response']['promotions']
		
		remote_promotions = [key['name'] for key in remote_promos]
		local_promotions = [key for key in promo.PROMOTIONS]
		self.assertEqual(remote_promotions, local_promotions,
						'Promotions list is not equal: {} != {}'.format(remote_promotions,local_promotions))
		#=======================================================================
		# Add a promotion to the deal
		#=======================================================================
		endpoint = '/api/merchant/promote/set'
		method = 'POST'
		post_url = base_url+endpoint+'?uid={uid}&levrToken={levrToken}&dealID={dealID}&receipt=psyck!_this_is_not_a_receipt!'.format(uid=uid,levrToken=levr_token,dealID=deal_id)
		
		#=======================================================================
		# # Boost rank
		#=======================================================================
		promotionID = promo.BOOST_RANK
		
		url = post_url+'&promotionID={promotionID}'.format(promotionID = promotionID)
		if refresh == True:
			data = self._fetch(url, method, endpoint,True)
			deal = data['response']['deal']
	#		pprint(deal)
			karma = deal['karma']
			print '--> karma: ', karma
			print '--> vote: ', deal['vote']
			print '--> promotions: ', deal['promotions']
			print '--> rank before: {}, rank after: {}'.format(pre_promotion_karma,karma)
			self.assertGreater(karma , pre_promotion_karma, 'rank did not change')
			
		
		# run a second time to make sure it fails
		self._fetch(url, method, endpoint, False)
		
		#=======================================================================
		# More tags!
		#=======================================================================
		new_tags = 'tag1,tag2,tag_one_million!,legal'
		promotionID = promo.MORE_TAGS
		url = post_url+'&promotionID={promotionID}&tags={tags}'.format(
																	promotionID=promotionID,
																	tags=new_tags
																	)
		if refresh == True:
			data = self._fetch(url, method, endpoint, True)
			deal = data['response']['deal']
			print '--> promotions: ', deal['promotions']

		# Run again to make sure it fails
		self._fetch(url, method, endpoint, False)
		#=======================================================================
		# Radius alert
		#=======================================================================
		promotionID = promo.RADIUS_ALERT
		url = post_url+'&promotionID={promotionID}'.format(
														promotionID=promotionID
														)
		if refresh == True:
			data = self._fetch(url, method, endpoint, True)
			deal = data['response']['deal']
			print '--> promotions: ', deal['promotions']
			assert promotionID in deal['promotions'], '{} alert not in the promotions'.format(promotionID)
		
		# Run again to make sure it fails
		self._fetch(url, method, endpoint, False)
		
		
		#=======================================================================
		# Notify previous likes
		#=======================================================================
		# need to have another like another deal uploaded by the business first
#		previous_like_dealID = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fCHGJdErv19TaoeLGNiu51StjnMAaChDyDrrMSui1aMhObO0DBg=='
		# Loughbrough university
		previous_like_uid = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51St8jOIaChA='
		previous_like_levr_token = '51OCPVtF51girDi2K01HytwOzpTWQjqFWrZjXgPDXDQ'
		
#		# Upvote another deal at the business
#		url = base_url+'/api/deal/{dealID}/upvote?uid={uid}&levrToken={levrToken}'.format(
#																						dealID=previous_like_dealID,
#																						uid=previous_like_uid,
#																						levrToken=previous_like_levr_token
#																						)
#		data = self._fetch(url, 'GET', '/api/deal/<dealID>/upvote', True)
		
		
		# Get the users old notifications to flush
		url = base_url+'/api/user/{previous_like_uid}/notifications?levrToken={previous_like_levr_token}'.format(
																				previous_like_uid=previous_like_uid,
																				previous_like_levr_token=previous_like_levr_token
																				)
		data = self._fetch(url, 'GET', '/api/user/<uid>/notifications', True)
		
		
		# Activate the previous like power up!
		promotionID = promo.NOTIFY_PREVIOUS_LIKES
		url = post_url+'&promotionID={promotionID}'.format(
														promotionID=promotionID
														)
		if refresh == True:
			data = self._fetch(url, method, endpoint, True)
			deal = data['response']['deal']
			print '--> promotions: ', deal['promotions']
			assert promotionID in deal['promotions'], '{} alert not in the promotions'.format(promotionID)
		
		# Run again to make sure it fails
		self._fetch(url, method, endpoint, False)
		
		
		if refresh == True:
			# fetch user notifications to make sure the notification was created correctly
			url = base_url+'/api/user/{previous_like_uid}/notifications?levrToken={previous_like_levr_token}'.format(
																					previous_like_uid=previous_like_uid,
																					previous_like_levr_token = previous_like_levr_token
																					)
			data = self._fetch(url, 'GET', '/api/user/<uid>/notifications', True)
			notifications = data['response']['notifications']
			num_notifications = data['response']['numResults']
		
			self.assertEqual(num_notifications, 1, 'User should have one notification, has {}'.format(num_notifications))
			pprint(notifications)
		#=======================================================================
		# Notify related likes
		#=======================================================================
#		related_likes_deal_id = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fCHGJdErv19TaoeLGNiu51Ss7n-IaChDyDrrMSui1aMhOM9UDBg==' # has tag 'legal'
		related_likes_uid = 'tAvwdQhJqgEn8hL7fD1phb9z_c-GNGaQXr0fO3GJdErv19TaoeLGNiu51Stnw-YaChA=' # Poop Scoops
		related_like_levr_token = '7VHUPQ1F4lh6rDi2K0VAxd0MzpOBRznWWeAzWgGSBTI'
		
		#=======================================================================
		# # Upvote the related deal
		# url = base_url+'/api/deal/{dealID}/upvote?uid={uid}&levrToken={levrToken}'.format(
		#																				dealID=related_likes_deal_id,
		#																				uid=related_likes_uid,
		#																				levrToken=related_like_levr_token
		#																				)
		# data = self._fetch(url, 'GET', '/api/deal/<dealID>/upvote', True)
		#=======================================================================
		
		# Get the users notifications to flush them
		url = base_url+'/api/user/{uid}/notifications?levrToken={levrToken}'.format(
																			uid=related_likes_uid,
																			levrToken=related_like_levr_token
																			)
		data = self._fetch(url, 'GET', '/api/user/<uid>/notifications', True)
		
		
		# Create the promotion!!
		promotionID = promo.NOTIFY_RELATED_LIKES
		url = post_url+'&promotionID={promotionID}'.format(
														promotionID=promotionID
														)
		if refresh == True:
			data = self._fetch(url, method, endpoint, True)
			deal = data['response']['deal']
			print '--> promotions: ', deal['promotions']
			assert promotionID in deal['promotions'], '{} alert not in the promotions'.format(promotionID)
		
		# Run again to make sure it fails
		self._fetch(url, method, endpoint, False)
		
		if refresh == True:
			# Get the users notifications to make sure the new one is there
			url = base_url+'/api/user/{uid}/notifications?levrToken={levrToken}'.format(
																				uid=related_likes_uid,
																				levrToken=related_like_levr_token
																				)
			data = self._fetch(url, 'GET', '/api/user/<uid>/notifications', True)
			notifications = data['response']['notifications']
			num_notifications = data['response']['numResults']
			
			self.assertEqual(num_notifications, 1, 'User should have one notification, has {}'.format(num_notifications))
			pprint(notifications)
		
	def _fetch(self,url,method,endpoint,success=True):
		if method == 'GET':
			post_data = None
		elif method == 'POST':
			post_data = '{}'
		
#		print url
		req = u.Request(url,post_data,{'Content-Type': 'application/json'})
		t1 = datetime.now()
		response = u.urlopen(req)
		t2 = datetime.now()
		tdiff = t2-t1
		print ' '
		print ' '
		print ' '
		print '--> ' + url
		print '--> ' + str(tdiff)
		
		self.assertEqual(response.code, 200, 'Response code {} on test search'.format(response.code))
		data = json.loads(response.read())
		
#		pprint(data.get('meta',None))
		
		meta = data['meta']
		if success == True:
			self.assertEqual(meta['success'], True, 'Call to {} returned error: "{}"'.format(url,meta.get('error','None')))
		elif success == False:
			self.assertEqual(meta['success'], False, 'Call to {} did not return error: \n{}'.format(url,pprint(data)))
			
#		pprint(data)
		return data
		
if __name__ == '__main__':
	
	print 'Running levr curl test on {}...'.format(base_url)
	
	unittest.main()
	