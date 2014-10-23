import webapp2
from templates import get_template
from models.settings import Settings

class AboutHandler(webapp2.RequestHandler):
	def get(self):
		Settings.get() #Force email address update...
		self.response.write(get_template('about.html').render({"page":"about"}))
