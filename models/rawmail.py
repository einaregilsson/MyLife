import datetime
from google.appengine.ext import ndb


class RawMail(ndb.Model):
	text = ndb.TextProperty()
	html = ndb.TextProperty()
	subject = ndb.StringProperty()
	sender = ndb.StringProperty()
	slug = ndb.StringProperty()
	date = ndb.DateProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)
