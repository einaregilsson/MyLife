import datetime
from google.appengine.ext import ndb


class ImportTask(ndb.Model):
	blob_key = ndb.BlobKeyProperty()
	total_posts = ndb.IntegerProperty(default=0)
	total_photos = ndb.IntegerProperty(default=0)
	imported_posts = ndb.IntegerProperty(default=0)
	imported_photos = ndb.IntegerProperty(default=0)
	created = ndb.DateTimeProperty(auto_now_add=True)
	updated = ndb.DateTimeProperty(auto_now=True)
	status = ndb.StringProperty(choices=['new', 'inprogress', 'finished', 'failed'],default='new')
	message = ndb.TextProperty()

	def update(self, message, **kwargs):
		self.message = message
		for k,v in kwargs.items():
			self.__setattr__(k, v)
		self.put()
