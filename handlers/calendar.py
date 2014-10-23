import webapp2
from templates import get_template

class CalendarHandler(webapp2.RequestHandler):
	def get(self):
		data = { "page" : "write"}
		self.response.write(get_template('calendar.html').render(data))

