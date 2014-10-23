import webapp2, logging
from models.postcounter import PostCounter
from models.post import Post
from google.appengine.api import users

class DataUpgradeHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		logging.info('LOGGED IN USER IS: %s' % user)


