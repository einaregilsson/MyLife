import datetime
from google.appengine.ext import ndb


class Slug(ndb.Model):
	slug = ndb.StringProperty()
	date = ndb.DateProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)
