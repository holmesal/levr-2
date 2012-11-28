from google.appengine.ext import db,ndb
import api_utils
import levr_classes as levr
import logging
import webapp2

class Keyword(ndb.Model):
	pass
	# key_name = stemmed Keyword
	def get_links(self):
		'''
		Fetches all keyword links for the provided Keyword name
		@param keyword: the name of the parent Keyword
		@type keyword: str
		'''
		links = KeywordLink.query(ancestor=ndb.Key(Keyword,self.key.string_id())).fetch(None)
		return links
class KeywordLink(ndb.Model):
	'''
	Unidirectional linkage from parent node to child
	This entity is always the child of a Keyword node
	The key_name/id of this entity is always the key_name/id of
		the receiving end of this link
		(we can do this because the parent is part of the identifier for entities)
	'''
	# parent = SearchNode
	# key_name = stemmed keyword
	strength = ndb.IntegerProperty(default=0)
	# can search for all links TO a certain node
	# cannot just search for by key name, because parent is part of key
	name = ndb.ComputedProperty(lambda self: self.key.string_id())
	
	@property
	def child_key(self):
		'''
		@return: The key of the receiving end of this linkage
		@rtype: ndb.Key
		'''
		# if we want to be able to query 
		return ndb.Key(Keyword,self.key.string_id())
	
class TestSearchHandler(api_utils.BaseClass):
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
			keyword_ids = [ndb.Key(Keyword,keyword) for keyword in search_tokens]
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
class TestResultClickHandler(api_utils.BaseClass):
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
			Linker.register_like(deal, query)
		self.response.out.write('\n\nDone!')
class Linker(object):
	# the relational weight that a click on a deal has
	_click_strength = 1
	# the relational weight that a like on a deal has
	_like_strength = 5
	# the relational weight that a manual categorization by admin has
	_admin_strength = 5
	
	@classmethod
	def register_deal_click(cls,deal,query):
		'''
		Registers a click on a deal that was found for a particular query
		@param query: the actual search term
		@type query: str
		@param deal: the deal entity that was clicked
		@type deal: levr.Deal
		'''
		strength = cls._click_strength
		cls._create_link_from_query(query, deal, strength)
	@classmethod
	def register_like(cls,deal,query):
		'''
		Registers a like on a deal from a particular query
		@param query: search term
		@type query: str
		@param deal: deal that was liked
		@type deal: levr.Deal
		'''
		
		strength = cls._like_strength
		cls._create_link_from_query(query, deal, strength)
	@classmethod
	def register_categorization(cls,deal,parent_tags):
		'''
		An admin manually categorized this deal, relating it to a list of tags
		@param deal: the deal that was 
		@type deal: levr.Deal
		@param tags: related (parent) tags
		@type tags: list
		'''
		strength = cls._admin_strength
		children_tags = deal.tags
		cls._create_link_to_tags_multi(parent_tags, children_tags, strength)
		
	@classmethod
	def _create_link_from_query(cls,query,deal,strength):
		'''
		Parses the query and creates link
		'''
		parent_tags = levr.create_tokens(query)
		children_tags = deal.tags
		cls._create_link_to_tags_multi(parent_tags, children_tags, strength)
	@classmethod
	def _create_link_to_tags_multi(cls,parent_tags,children_tags,strength):
		'''
		Wrapper for self.create_link_to_tags to handle multiple parent tags at once
		
		@warning: !!!parent_tags must be in their lowercase stemmed form!!!
		
		@param parent_tags: The tokenized search query
		@type parent_tags: list
		@param children_tags: the tags that are to be related to the parent tags
		@type children_tags: list
		'''
#		assert type(parent_tags) == list, 'parent_tags must be <type \'list\'>.'
		logging.info(parent_tags)
		# typecast parent_tags as list
		# otherwise, e.g. 'Food' will be broken up into 'f','o','o','d'
		if type(parent_tags) == str or type(parent_tags) == unicode:
			parent_tags = [parent_tags]
#		assert False, '{}:{}'.format(parent_tags,type(parent_tags))
		# remove duplicates
		
		parent_tags = list(set(parent_tags))
		
		for parent_tag in parent_tags:
			cls._create_link_to_tags(parent_tag, children_tags,strength)
		
	@classmethod
	def _create_link_to_tags(cls,parent_tag,children_tags,strength):
		'''
		Creates a one-way relationship linking the parent tag node to the children tags
		If the parent node does not exist yet, it creates it.
		If the link does not exist yet, it creates it.
		
		@param parent: the 'search term'
		@type parent: str
		@param children: the 'list of tags for the deals they clicked on'
		@type children: list
		'''
		# if the parent node does not exist, create it
		parent_node = Keyword.get_or_insert(parent_tag)
		
		assert parent_node, 'parent node not created'
#		try:
			# transactionally increment the 
		cls._increment_links(parent_node, children_tags,strength)
#		except:
#			# the transaction failed.
#			levr.log_error('Linkage failed for node: '+str(parent_tag))
#			return False
#		else:
#			return True
	@staticmethod
	@ndb.transactional(retries=10)
	def _increment_links(parent_node,children_tags,strength):
		'''
		Utility function to transactionally increment the strength of a given link
		If the transaction fails, the function is run again until it has success
		If the transaction fails too many times, it will raise an error
		
		If node links do not exist, they are created
		@param strength: The amount to increment the link strength by
		'''
		if type(children_tags) != list:
			children_tags = list(children_tags)
#		keys = [ndb.Key(Keyword,parent_node,)]
#		ndb.get_multi()
#		import random
#		strength = random.randint(1,30)
		node_links = [KeywordLink.get_or_insert(tag,parent=parent_node.key)
					for tag in children_tags]
		for link in node_links:
			link.strength += strength
		ndb.put_multi(node_links)
class ClearRelationsHandler(api_utils.BaseClass):
	def get(self):
		kws = Keyword.query().fetch(None)
		links = KeywordLink.query().fetch(None)
		ndb.delete_multi([kw.key for kw in kws])
		ndb.delete_multi([l.key for l in links])
		self.response.out.write('done!')
app = webapp2.WSGIApplication([
							('/sandbox', TestResultClickHandler),
							('/sandbox/search',TestSearchHandler),
							('/sandbox/clear', ClearRelationsHandler)
							
							],debug=True)