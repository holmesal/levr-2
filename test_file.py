#@PydevCodeAnalysisIgnore
#create tags list from the query
			tags = levr.tagger(query)
#			logging.info("tags: "+str(tags))
			
			#===================================================================
			# Init variables
			#===================================================================
			
			#variables
			precision		= 6
#			min_count		= 100
			max_iterations	= 3
			iterations		= 0
#			query_times		= []
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
			searched_hash_set	= [] #hashes that have been searched
			new_hash_set		= [] #hashes that havent been searched
			foursquare_ids		= []
			foursquare_deals	= []
			
			#===================================================================
			# Calculate the zoom level
			#===================================================================
#			top_right_lat = geo_point.lat + lat_half_delta
#			top_right_lon = geo_point.lon + lon_half_delta
#			bot_left_lat = geo_point.lat - lat_half_delta
#			bot_left_lon = geo_point.lon - lon_half_delta
			
			# If the zoom level was indicated, adjust the precision and size of the search box
			if lon_half_delta is not None:
				center_right_lat = geo_point.lat
				center_right_lon = geo_point.lon + lon_half_delta
				center_left_lat = geo_point.lat
				center_left_lon = geo_point.lon - lon_half_delta
				
	#			width_in_degrees = 2 * lat_half_delta
				width_in_miles = api_utils.distance_between_points(center_right_lat,center_right_lon,center_left_lat,center_left_lon)
				
				if width_in_miles < 2:
					precision = 6
				else:
					precision = 5
			else:
				precision = 5
			#===================================================================
			# Build set of geohashes to search
			#===================================================================
			logging.info('precision: {}'.format(precision))
			t1 = datetime.now()
			if precision == 5:
				new_hash_set = [geohash.encode(lat1,lon1,precision=precision)]
				total_hash_set = geohash.expand(new_hash_set[0])
			elif precision == 6:
				# center hash
				
				new_hash_set = [geohash.encode(lat1,lon1,precision=precision)]
				#iterate searches the specified number of times
				for i in range(0,max_iterations): #@UnusedVariable
					iterations += 1
					
					#expand range by one ring
					hashes = new_hash_set
					new_hash_set = []
					for ghash in hashes:
						#get hash neighbors
						#extend the hashes list with the new hashes
						new_hash_set.extend(geohash.expand(ghash))
					
					#remove duplicated
					new_hash_set = list(set(new_hash_set))
					#filter out the hashes that have already been searched
					new_hash_set = filter(lambda h: h not in searched_hash_set,new_hash_set)
					
					#new_hash_set is now a ring of geohashes around the last ring that was searched
					#add new_hash_set to searched_hash_set
					searched_hash_set.extend(new_hash_set)
					#reset new_hash_set
	#				logging.info('searched_hash_set: '+str(searched_hash_set))
				
				
				total_hash_set = searched_hash_set
			logging.info('total_hash_set: '+str(total_hash_set))
			t2 = datetime.now()
			geo_box_creation_time = t2-t1
			
			
			#===================================================================
			# Fetch deal keys from memcache or from query
			#===================================================================
			logging.debug('\n\n\n \t\t\t START QUERYING \n\n\n')
			query_start = datetime.now()
			deal_keys = api_utils.get_deal_keys(total_hash_set,development=development)
			query_end = datetime.now()
			
			total_query_time = query_end-query_start
			
			logging.debug('\n\n\n \t\t\t END QUERYING \n\n\n ')
			#===================================================================
			# Create Bounding Box
			#===================================================================
			
			#create bounding box from resulting new_hash_set - this is the outer set
			points = [geohash.decode(ghash) for ghash in total_hash_set]
			logging.info(points)
			#unzip lat,lons into two separate lists
			lat,lon = zip(*points)
			
			#find max lat, long
			max_lat = max(lat)
			max_lon = max(lon)
			#find min lat, long
			min_lat = min(lat)
			min_lon = min(lon)
			
			bottom_left_hash = geohash.encode(min_lat,min_lon,precision)
			
#			levr.geo_converter(str(min_lat)+','+str(min_lon))
			top_right_hash = geohash.encode(max_lat, max_lon, precision)
#			levr.geo_converter(str(max_lat)+','+str(max_lon))
			
			logging.info(top_right_hash)
			logging.info(bottom_left_hash)
			tr = geohash.bbox(top_right_hash)
			bl = geohash.bbox(bottom_left_hash)
			top_right = (tr['n'],tr['e'])
			bottom_left = (bl['s'],bl['w'])
			bounding_box = {
						'bottom_left'	: bottom_left,
#						'bot_left'		: (min_lat,min_lon),
						'top_right'		: top_right
#						'top_rt'		: (max_lat,max_lon),
#						'tr'			: tr,
#						'bl'			: bl
						}
			logging.debug(bounding_box)
			
			
			logging.info('total deals fetched: '+str((deal_keys.__len__())))
			#batch get all of the deals
			t1 = datetime.now()
			logging.debug(deal_keys)
			logging.debug(type(deal_keys))
			deals = db.get(deal_keys)
			t2 = datetime.now()
			
			fetch_time = t2-t1
			
			
			
			
			#===================================================================
			# Find karma maximums and deal maximums
			#===================================================================
			
			t1 = datetime.now()
			#find the max k and max d out of the deals that have been found
			for deal in deals:
				# get deal karma points
				#  karma is added when a business promotes the deal. Adds to rank, but doesnt show in upvotes
				k		= deal.upvotes - deal.downvotes + deal.karma
				try:
					if deal.origin == 'levr':
						k += 5
					else:
						pass
				except:
					levr.log_error('Deal origin')
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
			
			#===================================================================
			# Rank Deals
			#===================================================================
			
			t1 = datetime.now()
			#calculate the rank of all of the deals that have been found
			for idx,toop in enumerate(tuple_list):
				#rank = (1+kf)/df
				#toop = (rank,karma,distance,deal)
				k = toop[1]
				d = toop[2]
				deal = toop[3]
				
#				logging.debug('k:'+str(k)+', d: '+str(d)+', max_k: '+str(max_k)+', max_d: '+str(max_d))
				
				#calculate scaled karma and distance
				kf = k#k_coef*k/max_k
				df = d_coef*d/max_d
				
				#set minimum d... especially to eliminate division by zero
				if df < 0.05: df = 0.05
				
#				logging.debug('kf: '+str(kf)+', df: '+str(df))
				#===============================================================
				# #calculate rank
				# rank = (1+kf)/df
				#===============================================================
				# For now, it has been changed so that distance is not a factor in the ranking
				# The ranking system was meant to alleviate the density problem, but
				# we found that the distance factor only bunches deals that are close to the person
				# The algo was also based on an assuption that the distance is an important factor,
				# but a certain zoom level implies that the area that is shown is the primary area of interest,
				# and any point within the visible area is an acceptable point for a deal
				rank = (1+kf)
#				logging.debug('rank: '+str(rank))
				#add the rank to the deal toop
#				logging.debug(toop)
				toop = list(toop)
				toop[0] = rank
				toop = tuple(toop)
#				logging.debug(toop)
				
				tuple_list[idx] = toop
				
				
				
				
			t2 = datetime.now()
			
			calc_rank_time = t2-t1
			
			logging.debug('Tuple list:')
			logging.debug(tuple_list)
			
			
			#===================================================================
			# Filter deals by tag
			#===================================================================
			# if tags and tags[0] not in SPECIAL_QUERIES:
			#	#grab all deals where primary_cat is in tags
			#	for tag in tags:
			#		logging.debug('tag: '+str(tag))
			#		q.filter('tags =',tag)
			# else:
			#	pass
			
			accepted_deals_tuple_list = []
			
			if query != 'all':
				for toop in tuple_list:
					flag = False
					#toop[3] is the deal entity
					deal_tags = toop[3].tags
					for deal_tag in deal_tags:
						if deal_tag in tags:
							#flag that at least one of the tags on the deal match one of the query tags
							flag = True
					#after iterating through all deal tags, if at least one of the tags matched, add to the list of accepted deals
					if flag == True:
						accepted_deals_tuple_list.append(toop)
			else:
				logging.debug('All of the deals')
				accepted_deals_tuple_list = tuple_list
				
			
			logging.debug(accepted_deals_tuple_list)
			#count the results that matched the query
			accepted_deals_count = accepted_deals_tuple_list.__len__()
			if accepted_deals_count == 0:
				#no acceptable deals - empty response
				is_empty = True
			else:
				#there is at least one deal result
				is_empty = False
			
			#===================================================================
			# Package deals 
			#===================================================================
			#package deals
			t1 = datetime.now()
			#toop[3] is the deal
			#toop[0] is the rank
			logging.debug(accepted_deals_tuple_list)
			logging.debug(tuple_list)
			if is_empty == False:
				logging.debug('\n\n\t\t NOT EMPTY \n\n')
				#only package the deals that have a matching tag
				lst = accepted_deals_tuple_list
				
			else:
				logging.debug('\n\n\t\t EMPTY\n\n')
				#package all of the deals
				lst = tuple_list
#				packaged_deals = [api_utils.package_deal(toop[3],rank=toop[0],distance=toop[2]) for toop in tuple_list]
			
			# Only try to package deals if they are actually there
			if lst:
				# unzip list of tuples into various lists
				ranks,karmas,distances,deals = zip(*lst)
				logging.info(ranks)
				logging.info(karmas)
				logging.info(distances)
				logging.info(deals)
				
				#===============================================================
				# Check if any of the deals has a promotion 
				#===============================================================
				try:
					logging.info('checking for promotions')
					self.check_for_promotions(deals)
				except:
					levr.log_error()
				
				
				packaged_deals = api_utils.package_deal_multi(deals,ranks=ranks,distances=distances)
				
				# add deal views for each deal
				try:
					payload = {
							'deal_keys' : [str(deal.key()) for deal in deals]
							}
					taskqueue.add(url=INCREMENT_DEAL_VIEW_URL,payload=json.dumps(payload))
				except:
					levr.log_error()
				
			else:
				# No deals were found in the db at all!
				packaged_deals = []
			
			t2 = datetime.now()
			
			package_time = t2-t1
			
			
			t1= datetime.now()
>>>>>>> search
