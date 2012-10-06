import webapp2
import logging
import levr_encrypt as enc
import levr_classes as levr
import api_utils
import geo.geohash as geohash
from google.appengine.api import taskqueue
import json
from datetime import datetime
from google.appengine.ext import db



class SearchQueryHandler(webapp2.RequestHandler):
	@api_utils.validate('query',None,geoPoint=True,radius=False,user=False)
	def get(self,*args,**kwargs):
		'''
		inputs: lat,lon,limit, query
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				[string,string]
				}
		'''
		try:
			logging.debug('SEARCH BY QUERY\n\n\n')
	#		logging.debug(kwargs)
			#GET PARAMS
			logging.info(kwargs)
			geo_point 	= kwargs.get('geoPoint')
			radius 		= kwargs.get('radius')
			limit 		= kwargs.get('limit')
			query 		= kwargs.get('query','all')
			development = kwargs.get('development',False)
			foursquare	= kwargs.get('foursquare',False)
			user 		= kwargs.get('actor')
			
			#create tags from the query
			tags = levr.tagger(query)
			logging.info("tags: "+str(tags))
			
			#variables
			precision		= 5
			min_count		= 50
			deal_keys		= []
			max_iterations	= 3
			iterations		= 0
			query_times		= []
			max_k			= 0.1 #max karma count
			max_d			= 0.1 #max distance
			k_coef			= 1
			d_coef			= 1
			k_list			= []
			d_list			= []
			lat1			= geo_point.lat
			lon1			= geo_point.lon
			tstart			= datetime.now()
			tuple_list		= []
			searched_hash_set = [] #hashes that have been searched
			new_hash_set	= [] #hashes that havent been searched
			foursquare_ids = []
			
			
			
			#center hash
			new_hash_set = [geohash.encode(lat1,lon1,precision=precision)]
			query_start = datetime.now()
			#iterate searches the specified number of times
			for i in range(0,max_iterations):
				#if the deals fetches are less than the desired minimum, perform another search
				if deal_keys.__len__() <= min_count:
					iterations += 1
#					logging.debug('\n\n\n\n\n\n begin new hashings\n\n\n\n\n\n\n')
#					logging.debug(searched_hash_set)
#					logging.debug(new_hash_set)
					
					#expand range by one ring
					hashes = new_hash_set
					new_hash_set = []
					for hash in hashes:
						#get hash neighbors
						#extend the hashes list with the new hashes
						new_hash_set.extend(geohash.expand(hash))
					
					#remove duplicated
					new_hash_set = list(set(new_hash_set))
					#filter out the hashes that have already been searched
					new_hash_set = filter(lambda h: h not in searched_hash_set,new_hash_set)
					
					#new_hash_set is now a ring of geohashes around the last ring that was searched
					
					
					#fetch deals from hash set, and extend the list of deal keys
					t1 = datetime.now()
					deal_keys.extend(api_utils.get_deal_keys_from_hash_set(tags,new_hash_set,development=development,foursquare=foursquare))
					t2 = datetime.now()
					
					#add new_hash_set to searched_hash_set
					searched_hash_set.extend(new_hash_set)
					#reset new_hash_set
					logging.info('searched_hash_set: '+str(searched_hash_set))
#					logging.debug('\n\n\n\n\n\n end new hashings\n\n\n\n\n\n\n')
					#keep track of the times
					query_times.append((t1,t2))
			query_end = datetime.now()
			
			total_query_time = query_end-query_start
			
			#create bounding box from resulting new_hash_set
			points = [geohash.decode(hash) for hash in new_hash_set]
			logging.debug(points)
			#unzip lat,lons into two separate lists
			lat,lon = zip(*points)
			
			#find max lat, long
			max_lat = max(lat)
			max_lon = max(lon)
			#find min lat, long
			min_lat = min(lat)
			min_lon = min(lon)
			
			#create bounding box
			bounding_box = {
						'bottom_left'	: (min_lat,min_lon),
						'top_right'		: (max_lat,max_lon)
						}
			logging.debug(bounding_box)
			
			
			logging.info('total deals fetched: '+str((deal_keys.__len__())))
			#batch get all of the deals
			t1 = datetime.now()
			deals = db.get(deal_keys)
			t2 = datetime.now()
			
			fetch_time = t2-t1
			
			
			t1 = datetime.now()
			#find the max k and max d out of the deals that have been found
			for deal in deals:
				#get deal karma points = upvotes for now
				k		= deal.upvotes - deal.downvotes
				k_list.append(k)
#				logging.debug('deal karma: '+str(k))
				
				#calculate the distance between the request point and the deal
				lat2	= deal.geo_point.lat
				lon2	= deal.geo_point.lon
				d		= api_utils.distance_between_points(lat1,lon1,lat2,lon2)
				d_list.append(d)
#				logging.debug('distance: '+str(d))
				
				#if this deal has a greater karma, then set it as the max k
				if k > max_k: max_k = k
				#if this deal is farther away than the farthest one so far, set it as the max d
				if d > max_d: max_d = d
				
				#compile into tuple
				#toop = (rank,karma,distance,deal)
				toop = (0.0,k,d,deal)
				tuple_list.append(toop)
				
				#append foursquare id
				if deal.foursquare_id:
					foursquare_ids.append(deal.foursquare_id)
			t2 = datetime.now()
			
			calc_maxes_time = t2-t1
			
#			logging.debug('Tuple list:')
#			logging.debug(tuple_list)
			
			t1 = datetime.now()
			#calculate the rank of all of the deals that have been found
			for idx,toop in enumerate(tuple_list):
				#rank = (1+kf)/df
				#toop = (rank,karma,distance,deal)
				k = toop[1]
				d = toop[2]
				deal = toop[3]
				
				logging.debug('k:'+str(k)+', d: '+str(d)+', max_k: '+str(max_k)+', max_d: '+str(max_d))
				
				#calculate scaled karma and distance
				kf = k_coef*k/max_k
				df = d_coef*d/max_d
				
				#set minimum d... especially to eliminate division by zero
				if df < 0.05: df = 0.05
				
				logging.debug('kf: '+str(kf)+', df: '+str(df))
				#calculate rank
				rank = (1+kf)/df
				logging.debug('rank: '+str(rank))
				#add the rank to the deal toop
#				logging.debug(toop)
				toop = list(toop)
				toop[0] = rank
				toop = tuple(toop)
#				logging.debug(toop)
				
				ts = datetime.now()
				tuple_list[idx] = toop
				te = datetime.now()
				logging.debug('replacement: '+str(te-ts))
				
				
				
				
			t2 = datetime.now()
			
			calc_rank_time = t2-t1
			
			logging.debug('Tuple list:')
			logging.debug(tuple_list)
			
			
			
			#package deals
			t1 = datetime.now()
			#toop[3] is the deal
			#toop[0] is the rank
			packaged_deals = [api_utils.package_deal(toop[3],rank=toop[0]) for toop in tuple_list]
			t2 = datetime.now()
			
			package_time = t2-t1
			
			tend = datetime.now()
			total_time = tend-tstart
			
			
			
			logging.debug('total_query_time: '+str(total_query_time))
			logging.debug('fetch_time: '+str(fetch_time))
			logging.debug('calc_maxes_time: '+str(calc_maxes_time))
			logging.debug('calc_rank_time: '+str(calc_rank_time))
			logging.debug('package_time: '+str(package_time))
			logging.debug('total_time: '+str(total_time))
			
			#search foursquare for more results
			if user:
				if user.foursquare_token:
					#if len(results) < 5:
					if False:
						#not a lot of results, do the foursquare search in real-time
						ft1 = datetime.now()
						logging.info('FOURSQUARE IDS::::')
						logging.info(foursquare_ids)
						logging.debug('searching foursquare!')
						foursquare_deals = api_utils.search_foursquare(geo_point,user,foursquare_ids)
						logging.info('Levr results found: '+str(len(packaged_deals)))
						logging.info('Foursquare results found: '+str(len(foursquare_deals)))
						packaged_deals = packaged_deals + foursquare_deals
						logging.info('Total results found: '+str(len(packaged_deals)))
						ft2 = datetime.now()
						logging.info('Foursquare fetch time: ' + str(ft2-ft1))
					else:
						#lots of results, do the foursquare search inside a task
						params = {
							'lat'			:	geo_point.lat,
							'lon'			:	geo_point.lon,
							'userID'		:	str(user.key()),
							'foursquare_ids':	foursquare_ids
						}
						
						logging.debug('Sending this to the task: ' + json.dumps(params))
						
						#start the task
						t = taskqueue.add(url='/tasks/searchFoursquareTask',payload=json.dumps(params))

			
			response = {
					'numResults'		: packaged_deals.__len__(),
					'total_query_time'	: str(total_query_time),
					'fetch_time'		: str(fetch_time),
					'calc_maxes_time'	: str(calc_maxes_time),
					'cals_rank_time'	: str(calc_rank_time),
					'package_time'		: str(package_time),
					'total_time'		: str(total_time),
					'iterations'		: str(iterations),
					'boundingBox'		: bounding_box,
#					'ending_hashes'		: list(searched_hash_set),
					'ending_hash_length': list(searched_hash_set).__len__(),
					'deals'				: packaged_deals
					}
			
			
			#add yipit call if no deals are returned
			if len(packaged_deals) == 0:
				packaged_deals = packaged_deals + api_utils.search_yipit(query,geo_point)
				#update response
				#this will return a numResults of 0 - meaning all the deals are daily deals
				response.update({
					'deals'		:	packaged_deals
				})
			
			
			api_utils.send_response(self,response)
					
					
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')
			
			
class SearchNewHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,*args,**kwargs):
		'''
		inputs: lat,lon,limit,radius
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				[string,string]
				}
		'''
		try:
			logging.info("\n\nSEARCH NEW")
			
		except:
			levr.log_error(levr.log_dir(self.request))
			api_utils.send_error(self,'Server Error')

class SearchHotHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,*args,**kwargs):
		'''
		inputs: lat,lon,limit
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				[string,string]
				}
		'''
		try:
			pass
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')
class SearchPopularHandler(webapp2.RequestHandler):
	@api_utils.validate(None,None,geoPoint=True,limit=False,radius=False,user=False)
	def get(self,**kwargs):
		'''
		inputs: lat,lon,limit
		Output:{
			meta:{
				success
				errorMsg
				}
			response:{
				searches :[string,string]
				}
		'''
		try:
			logging.info('SEARCH POPULAR\n\n\n')
			#GET PARAMS
			request_point 	= kwargs.get('geoPoint')
			radius 		= kwargs.get('radius')
			limit 		= kwargs.get('limit')
			
			logging.debug("request_point type: "+str(type(request_point)))
			logging.debug('')
			deals = []
			t1 = datetime.now()
			#fetch deals
			#hash the reuqested geo_point
			center_hash = geohash.encode(request_point.lat,request_point.lon,precision=5)
			logging.debug(center_hash)
			
			#get the hashes of the center geo_point and the 8 surrounding hashes
			hash_set = geohash.expand(center_hash)
			logging.debug(hash_set)
			
			for query_hash in hash_set:
				#only grab keys for deals that have active status
				q = levr.Deal.all(projection=['tags']).filter('deal_status =','test')
				#FILTER BY GEOHASH
				q.filter('geo_hash >=',query_hash).filter('geo_hash <=',query_hash+"{") #max bound
				
#				logging.debug(levr.log_dir(q))
				#FETCH DEAL KEYS
				fetched_deals = q.fetch(None)
				logging.info('From: '+query_hash+", fetched: "+str(fetched_deals.__len__()))
				
				deals.extend(fetched_deals)
		#					logging.debug(deal_keys)
			t2 = datetime.now()
			
			
			#FILTER
			tags = []
			for deal in deals:
#				logging.debug(dir(deals))
				tags.extend(deal.tags)
			logging.debug(tags)
			
			#convert list of all tags to a dict of key=tag, val=frequency
			count = {}
			for tag in tags:
#					logging.debug(tag in count)
				if tag in count:
					count[tag] += 1
				else:
					count[tag] = 1
			
			#convert dict of tag:freq into list of tuples
			tuple_list = []
			for key in count:
				tuple_list.append((count[key],key))
				
			#sort tags by frequency, highest first
			tuple_list.sort()
			tuple_list.reverse()
			
			#select only the most popular ones, and convert to list
			word_list = [x[1] for x in tuple_list]
			
			#if the popular items list is longer than 6, send entire list, else only send 6
			logging.debug(word_list.__len__())
			if word_list.__len__()<6:
				popular_items = word_list
			else:
				popular_items = word_list[:6]
			
			#BATCH GET RESULTS
			t3 = datetime.now()
			
			
			
			#create response dict
			response = {
					'numResults': popular_items.__len__(),
					'fetching'	: str(t2-t1),
					'packaging'	: str(t3-t2),
					'total'		: str(t3-t1),
					'searches'	: popular_items
					}
			api_utils.send_response(self,response)
		except:
			levr.log_error(self.request.params)
			api_utils.send_error(self,'Server Error')

		
app = webapp2.WSGIApplication([(r'/api/search/new', SearchNewHandler),
								('/api/search/hot', SearchHotHandler),
								('/api/search/popular', SearchPopularHandler),
								('/api/search/(.*)', SearchQueryHandler)
								],debug=True)