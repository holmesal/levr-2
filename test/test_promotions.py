import unittest
import api_utils
import webapp2
from google.appengine.ext import testbed
from google.appengine.api import memcache
import webtest

class CacheHandler(webapp2.RequestHandler):
	def post(self):
		key = self.request.get('key')
		value = self.request.get('value')
		memcache.set(key, value) #@UndefinedVariable

class testPromotion(unittest.TestCase):
	def setUp(self):
		app = webapp2.WSGIApplication([('/cache/',CacheHandler)])
		self.testapp = webtest.TestApp(app)
		self.testbed = testbed.Testbed()
		self.testbed.activate()
	
	def tearDown(self):
		self.testbed.deactivate()
	
	def testCacheHandler(self):
		# First define a key and value to be cached.
		key = 'answer'
		value = '42'
		self.testbed.init_memcache_stub()
		params = {'key': key, 'value': value}
		# Then pass those values to the handler.
		response = self.testapp.post('/cache/', params)
		# Finally verify that the passed-in values are actually stored in Memcache.
		self.assertEqual(value, memcache.get(key)) #@UndefinedVariable