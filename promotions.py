BOOST_RANK = 'com.Levr.LevrForMerchants.boost_rank2'
# needs: deal


MORE_TAGS = 'com.Levr.LevrForMerchants.more_tags'
# needs: deal, tags

RADIUS_ALERT = 'com.Levr.LevrForMerchants.radius_alert'
RADIUS_ALERT_RADIUS = 5 #miles
# needs: deal, length of time for deal upload, radius

NOTIFY_PREVIOUS_LIKES = 'com.Levr.LevrForMerchants.notify_previous_likes'
# needs: deal

NOTIFY_RELATED_LIKES = 'com.Levr.LevrForMerchants.notify_related_likes'
# needs: deal, radius of effect - need to start adding searched_geohashes to a user entity

_img_url = 'http://www.levr.com/img/levr.png'
PROMOTIONS = {
			BOOST_RANK:{
					'name'	: BOOST_RANK,
					'img'	: 'http://25.media.tumblr.com/avatar_fdd788513051_128.png',
					'description' : 'Appear as a priority search result', # TODO: add description
					'color' : 'hex_code' # TODO: add colors to promotions
					},
			MORE_TAGS :{
					'name'	: MORE_TAGS,
					'img'	: 'http://a0.twimg.com/profile_images/1610510720/ugly_reasonably_small.jpg',
					'description' : 'Appear in more searches',
					'color' : 'hex_code'
					},
			RADIUS_ALERT : {
						'name'	: RADIUS_ALERT,
						'img'	: 'http://www.funnypica.com/wp-content/uploads/2012/05/Ugly-and-Crazy-Man.jpg',
						'description' : 'Alert customers in your area',
						'color' : 'hex_code'
						},
			NOTIFY_PREVIOUS_LIKES:{
								'name'	: NOTIFY_PREVIOUS_LIKES,
								'img'	: 'http://f-e-a-r-forums.2310788.n4.nabble.com/file/n4151751/ugly-fat-girl-bikini-old-woman-pictures.jpg',
								'description' : 'Alert customers who have visited you before',
								'color' : 'hex_code'
								},
			NOTIFY_RELATED_LIKES:{
								'name'	: NOTIFY_RELATED_LIKES,
								'img'	: 'http://upload.wikimedia.org/wikipedia/en/4/40/Atmosphere_God_Loves_Ugly.jpg',
								'description' : 'Alert customers who have liked similar deals',
								'color' : 'hex_code'
								}
			}
