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
					'readableName' : 'Rank Boost',
					'img'	: 'http://www.levr.com/img/promo_rank.png',
					'img2x' : 'http://www.levr.com/img/promo_rank_2x.png',
					'description' : 'Appear as a priority search result',
					},
			MORE_TAGS :{
					'name'	: MORE_TAGS,
					'readableName' : 'Search Tags',
					'img'	: 'http://www.levr.com/img/promo_tags.png',
					'img2x'	: 'http://www.levr.com/img/promo_tags_2x.png',
					'description' : 'Appear in more searches',
					},
			RADIUS_ALERT : {
						'name'	: RADIUS_ALERT,
						'readableName' : 'Radius Alert',
						'img'	: 'http://www.levr.com/img/promo_radius.png',
						'img2x'	: 'http://www.levr.com/img/promo_radius_2x.png',
						'description' : 'Alert customers in your area',
						},
			NOTIFY_PREVIOUS_LIKES:{
								'name'	: NOTIFY_PREVIOUS_LIKES,
								'readableName' : 'Good Taste',
								'img'	: 'http://www.levr.com/img/promo_likes.png',
								'img2x'	: 'http://www.levr.com/img/promo_likes_2x.png',
								'description' : 'Alert customers who have visited you before',
								},
			NOTIFY_RELATED_LIKES:{
								'name'	: NOTIFY_RELATED_LIKES,
								'readableName' : 'Notify Fans',
								'img'	: 'http://www.levr.com/img/promo_similar.png',
								'img2x'	: 'http://www.levr.com/img/promo_similar_2x.png',
								'description' : 'Alert customers who have liked similar deals',
								}
			}
