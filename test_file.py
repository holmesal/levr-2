from google.appengine.ext import db,ndb
import api_utils
import levr_classes as levr
import logging
import webapp2


	
class TestSearchHandler(api_utils.BaseHandler):
	@api_utils.validate(None, None,
					query = True,
					ll = True
					)
	def get(self,*args,**kwargs):
		query = kwargs.get('query')
		geo_point= kwargs.get('geoPoint')
		try:
			self.response.headers['Content-Type'] = 'text/plain'
			#===================================================================
			# Step 1: grab all of the deals...
			#===================================================================
			development = False
			search = api_utils.Search(development)
			# calc precision
			precision = 5
			# create ghashes
			ghash_list = search.create_ghash_list(geo_point, precision)
			# fetch all deals in the ghash range
			deals = search.fetch_deals(ghash_list)
			
			#===================================================================
			# Step 2: filter by query
			#===================================================================
			# tokenize the search query
			stemmed = True
			filtered = True
			search_tokens = levr.create_tokens(query, stemmed, filtered)
			self.response.out.write(search_tokens)
			#===================================================================
			# Tier 1: literal search results
			#===================================================================
			# find search matches
			# [(match count, deal), ]
			literal_toops = search.filter_deals_by_tags(deals,*search_tokens)
			tier1_ranks,deals = zip(*literal_toops)
			#===================================================================
			# Search Nodes
			#===================================================================
			
			# Remove all the kewords that dont have node entries. They are irrelevant
			keyword_ids = [ndb.Key(levr.KWNode,keyword) for keyword in search_tokens]
			self.response.out.write(keyword_ids)
			self.response.out.write(keyword_ids[0].get())
			keyword_nodes = ndb.get_multi(keyword_ids)
			self.response.out.write(keyword_nodes)
			# remove keys that do no have nodes
			kws = filter(None, keyword_nodes)
			self.response.out.write(kws)
			#===================================================================
			# # Create master list of all the linked kws and their strengths
			#===================================================================
			linked_kws = {}
			for kw in kws:
				links = kw.get_links()
				# normalize the link strengths by dividing by the maximum strength
				link_strengths = [link.strength for link in links]
				logging.info(link_strengths)
				if not link_strengths:
					assert False, "no link strengths"
					# TODO: handle this case
				max_strength = max(link_strengths)
				logging.info(max_strength)
				for link in links:
					norm_strength = float(link.strength)/float(max_strength)
					
					
					link_name = link.name
					# If the link name is not already in the list of kws, add it
					try:
						linked_kws[link_name] += norm_strength
					except:
						linked_kws.update({link_name:norm_strength})
			self.response.out.write(levr.log_dict(linked_kws))
			# should have a dict of strengths
			
			#===================================================================
			# # Rank the deals again by related link strength
			#===================================================================
			tier2_ranks = []
			for deal in deals:
				tier2_rank = 0
				for tag in deal.tags:
					if tag in linked_kws:
						tier2_rank += linked_kws[tag]
				tier2_ranks.append(tier2_rank)
			
			deals_tuples = zip(tier1_ranks,tier2_ranks,deals)
			
			deals_tuples = sorted(deals_tuples,reverse=True)
			
			
			tier1_ranks,tier2_ranks,deals = zip(*deals_tuples)
			for dt in deals_tuples:
				self.response.out.write('\n{}, {}, {}'.format(dt[0],dt[1],dt[2].tags))
#			self.response.out.write('\n'.join([str(dt) for dt in deals_tuples]))
			
			
			
			
			
		except Exception,e:
			self.send_fail(e)
class TestResultClickHandler(api_utils.BaseHandler):
#	@api_utils.validate(None, None,
#					query = True,
##					clicked = True,
#					deal = True,
#					user = True,
#					levrToken = True
#					)
	def get(self,*args,**kwargs):
		'''
		
		'''
		self.response.headers['Content-Type'] = 'text/plain'
		# SPOOF
		query = 'Food'
		deals = []
		tags = ['drink','coffe','lunch','appet','bar']
		for t in tags:
			deals.extend(levr.Deal.all().filter('tags',t).fetch(None))
		deals = list(set(deals))
		self.response.out.write('\n\t\t\t<===================>\n'.join([levr.log_model_props(deal, ['deal_text','description']) for deal in deals]))
#		deal.tags = ['tagggg']
		# /SPOOF
#		assert False, deals
#		parent_tags = levr.create_tokens(query)
#		for deal in deals:
#			Linker.register_categorization(deal, parent_tags)
#		for deal in deals:
#			Linker.register_deal_click(deal, query)
		for deal in deals:
			api_utils.KWLinker.register_like(deal, query)
		self.response.out.write('\n\nDone!')

class ClearRelationsHandler(api_utils.BaseHandler):
	def get(self):
		kws = levr.KWNode.query().fetch(None)
		links = levr.KWLink.query().fetch(None)
		ndb.delete_multi([kw.key for kw in kws])
		ndb.delete_multi([l.key for l in links])
		self.response.out.write('done!')
app = webapp2.WSGIApplication([
							('/sandbox', TestResultClickHandler),
							('/sandbox/search',TestSearchHandler),
							('/sandbox/clear', ClearRelationsHandler)
							
							],debug=True)