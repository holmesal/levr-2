from google.appengine.ext import db,ndb
import api_utils
import levr_classes as levr
import logging
import webapp2
from collections import Counter,defaultdict
import itertools
import operator
from datetime import datetime



def add_click(user,deal,click):
#	user = db.get(db.Key.from_path('Customer','pat'))
#	click = levr.DealClick.all().ancestor(user).get()
	if deal.key() not in click.deals:
		click.deals.append(deal.key())
	click.put()
	
	
class AddClickHandler(api_utils.BaseHandler):
	def get(self):
		user = db.get(db.Key.from_path('Customer','pat'))
		deals = levr.Deal.all().fetch(10)
		
		deal_click = levr.DealClick.get_or_insert('shard1',parent=user)
		
		for deal in deals:
			add_click(user, deal,deal_click)
		for deal in deals[:2]:
			user.upvotes.append(deal.key())
		db.put(user)
		self.say('Done!!')

class GetRecommendationHandler(api_utils.BaseHandler):
	def get(self):
		t0 = datetime.now()
		self.response.headers['Content-Type'] = 'text/plain'
		user = db.get(db.Key.from_path('Customer','pat'))
		
		# grab deal entities
		deal_clicks = levr.DealClick.all().ancestor(user).fetch(None)
		assert deal_clicks.__len__() == 1, deal_clicks.__len__()
		
		# fetch deals from the sharded deal_clicks
		click_lists = [click.deals for click in deal_clicks]
		unique_deal_keys = list(itertools.chain(*click_lists))
		deals = db.get(unique_deal_keys)
		
		# also would need to grab the deals from the upvotes,
		# but this is simulated and all clicked deals are upvoted
		# separate upvoted deals from clicked deals
		
		
		
		
		upvoted_deals = filter(lambda x: x.key() in user.upvotes, deals)
		clicked_deals = filter(lambda x: x.key() not in upvoted_deals, deals)
		
		upvote_tags = []
		for deal in upvoted_deals:
			upvote_tags.extend(deal.tags)
		
		clicked_tags = []
		for deal in clicked_deals:
			clicked_tags.extend(deal.tags)
		
		# weighted rank of each tag
		ranks = defaultdict(int)
		for tag in upvote_tags:
			ranks[tag] += 5
		for tag in clicked_tags:
			ranks[tag] += 1
		# remove factory from the defaultdict
		ranks.default_factory = None
		
		# at this point, we are in the same position as during a search where things are ranked by linked kw
		
		sorted_ranks = sorted(ranks.iteritems(),key=operator.itemgetter(1),reverse=True)
		
		
		self.say(levr.log_dict(ranks))
		self.say(sorted_ranks)
		
		
		
		
		
		self.say('\n\n\n')
		self.say(datetime.now()-t0)
#		upvote_tag_freqs = Counter(upvote_tags)
#		click_tag_freqs = Counter(clicked_tags)
#		
#		
#		self.say(levr.log_dict(upvote_tag_freqs))
#		self.say(levr.log_dict(click_tag_freqs))
#		
		



#class ClearRelationsHandler(api_utils.BaseHandler):
#	def get(self):
#		kws = levr.KWNode.query().fetch(None)
#		links = levr.KWLink.query().fetch(None)
#		ndb.delete_multi([kw.key for kw in kws])
#		ndb.delete_multi([l.key for l in links])
#		self.response.out.write('done!')
app = webapp2.WSGIApplication([
							('/sandbox/clicks',AddClickHandler),
							('/sandbox/recommend',GetRecommendationHandler)
#							('/sandbox/clear', ClearRelationsHandler)
							
							],debug=True)