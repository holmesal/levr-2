import os
import webapp2
import jinja2
from datetime import date,timedelta

import logging


import mixpanel
import mixmap

class MixMapHandler(webapp2.RequestHandler):
	def get(self):
		
# 		data = mixmap.grab('Last Login',100000,'0bff6b03e7955b8e1df08a8ec0828c9f','06a9d35b90bc1a1b8035394cd295faff')
		
		days = self.request.get('days',5)
		start_date = date.today()-timedelta(days=int(days))
		
		api = mixpanel.Mixpanel(api_key='0bff6b03e7955b8e1df08a8ec0828c9f',api_secret='06a9d35b90bc1a1b8035394cd295faff')
		
		data = api.request(['segmentation'], {
			'event' : 'Search',
			'from_date'	: start_date.isoformat(),
			'to_date'	: date.today().isoformat(),
			'on'	: 'properties["Location"]',
			'where' 	: 'properties["Expanded"] == boolean("false")'
		})
		
		features = []
		lats = []
		lons = []
		events = []
		
		for point in data['data']['values']:
			feature = {
					"geometry"		:	{
						"type"			:	"Point",
						"coordinates"	:	[float(point.split(',')[1]),float(point.split(',')[0])]
					},	
					"properties"	:	{
						"events"	:	sum(data['data']['values'][point].values())
					}
			}
			
			features.append(feature)
			lats.append(feature["geometry"]["coordinates"][1])
			lons.append(feature["geometry"]["coordinates"][0])
			events.append(feature["properties"]["events"])
		
		
		#max,min, and scale
		events_max = max(events)
		logging.info(events_max)
		for feature in features:
			feature["properties"]["scale"] = float(feature["properties"]["events"])/float(events_max)
		
		#build output
		output = {
			"extent"	:	[
				{"lat":float(min(lats)),"lon":float(min(lons))},
				{"lat":float(max(lats)),"lon":float(max(lons))}
			],
			"days":days,
			"features"	:	features
		}
		
		logging.info(output)
		
 		#launch the jinja environment
		jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		template = jinja_environment.get_template('templates/mixmap.html')
		self.response.out.write(template.render(output))


app = webapp2.WSGIApplication([('/mixmap',MixMapHandler)])