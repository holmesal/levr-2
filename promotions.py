BOOST_RANK = 'boost_rank'
# needs: deal


MORE_TAGS = 'more_tags'
# needs: deal, tags

RADIUS_ALERT = 'radius_alert'
# needs: deal, length of time for deal upload

NOTIFY_PREVIOUS_LIKES = 'notify_previous_likes'
# needs: deal

NOTIFY_RELATED_LIKES = 'notify_related_likes'
# needs: deal, radius of effect - need to start adding searched_geohashes to a user entity

PROMOTIONS = {
			BOOST_RANK:{
					'name'	: BOOST_RANK,
					'img'	: 'IMAGE'
					},
			MORE_TAGS :{
					'name'	: MORE_TAGS,
					'img'	: 'IMAGE!!'
					},
			RADIUS_ALERT : {
						'name'	: RADIUS_ALERT,
						'img'	: 'IMAGE'
						},
			NOTIFY_PREVIOUS_LIKES:{},
			NOTIFY_RELATED_LIKES:{}
			}
# TODO: talk with ethan about what exactly is necessary to send 