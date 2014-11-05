import datetime
from google.appengine.ext import ndb
from models.timezones import timezones
from google.appengine.api import users

class Settings(ndb.Model):
	email_address = ndb.StringProperty(required=True)
	timezone = ndb.StringProperty(default="America/Los_Angeles")
	email_hour = ndb.IntegerProperty(default=20)
	include_old_post_in_entry = ndb.BooleanProperty(default=True)
	dropbox_access_token = ndb.StringProperty(required=False)
	dropbox_last_backup = ndb.DateTimeProperty(required=False)
	
	@classmethod
 	def get(cls):
 		settings = cls.query().get() or Settings()

 		if not settings.email_address:
 			#If the user is logged in we'll save his email address...
 			user = users.get_current_user()
 			if user:
 				settings.email_address = user.email()
 				settings.put()

 		return settings
