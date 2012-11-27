import os
import webapp2
import jinja2
from datetime import date,datetime,timedelta

import logging
from levr_classes import log_dict


import mixpanel



class AnalyticsHandler(webapp2.RequestHandler):
	def get(self):
		
# 		data = mixmap.grab('Last Login',100000,'0bff6b03e7955b8e1df08a8ec0828c9f','06a9d35b90bc1a1b8035394cd295faff')
		
		days = self.request.get('days',0)
		start_date = date.today()-timedelta(days=int(days))
		
		api = mixpanel.Mixpanel(api_key='0bff6b03e7955b8e1df08a8ec0828c9f',api_secret='06a9d35b90bc1a1b8035394cd295faff')
		
		# data = api.request(['segmentation'], {
# 			'event' : 'Search',
# 			'from_date'	: start_date.isoformat(),
# 			'to_date'	: date.today().isoformat(),
# 			'on'	: 'properties["Location"]',
# 			'where' 	: 'properties["Expanded"] == boolean("false")'
# 		})
		
		#how many signups in the date range?
		data = api.request(['segmentation'], {
			'event' : 'Signup Success',
			'from_date'	: start_date.isoformat(),
			'to_date'	: date.today().isoformat()
		})
		
		signups = sum(data['data']['values']['Signup Success'].values())
		logging.info("Signups: "+str(signups))
		
		
		#how many searches in the date range?
		data = api.request(['segmentation'], {
			'event' : 'Search',
			'from_date'	: start_date.isoformat(),
			'to_date'	: date.today().isoformat()
		})
		
		searches = sum(data['data']['values']['Search'].values())
		logging.info("Searches: "+str(searches))
		
		
		#how many non-expanded searches in the date range?
		data = api.request(['segmentation'], {
			'event' : 'Search',
			'from_date'	: start_date.isoformat(),
			'to_date'	: date.today().isoformat(),
			'where' 	: 'properties["Expanded"] == boolean("false")'
		})
		
		searches_non_exp = sum(data['data']['values']['Search'].values())
		logging.info("Non-expanded searches: "+str(searches_non_exp))
		
		#how many deal uploads in the date range?
		data = api.request(['segmentation'], {
			'event' : 'Share Done',
			'from_date'	: start_date.isoformat(),
			'to_date'	: date.today().isoformat()
		})
		
		uploads = sum(data['data']['values']['Share Done'].values())
		logging.info("Deals uploaded: "+str(uploads))
		
		
		#how many daily active users?
		#grab all the users
		data = api.request(['engage'],{})
		#take only those that actually have a last seen property
		users = [x for x in data['results'] if '$last_seen' in x['$properties']]
		
		now = datetime.now()
		t_daily = now - timedelta(days=1)
		t_monthly = now - timedelta(days=30)
		
		daily = [x for x in users if datetime.strptime(x['$properties']['$last_seen'],'%Y-%m-%dT%H:%M:%S') > t_daily]
		monthly = [x for x in users if datetime.strptime(x['$properties']['$last_seen'],'%Y-%m-%dT%H:%M:%S') > t_monthly]
		
		dau_mau = float(len(daily))/float(len(monthly))*100
		
		template_values = {
			"signups"			:	signups,
			"searches"			:	searches,
			"searches_non_exp"	:	searches_non_exp,
			"uploads"			:	uploads,
			"dau_mau"			:	"%.2f" % dau_mau,
			"daily"			:	len(daily),
			"monthly"			:	len(monthly)
		}
		
		logging.info(log_dict(template_values))
		
 		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/analytics.html')
		self.response.out.write(template.render(template_values))


app = webapp2.WSGIApplication([('/analytics',AnalyticsHandler)])