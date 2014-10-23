import datetime
from google.appengine.ext import ndb


class ExportTask(ndb.Model):
	blob_key = ndb.BlobKeyProperty()
	total_posts = ndb.IntegerProperty(default=0)
	total_photos = ndb.IntegerProperty(default=0)
	exported_posts = ndb.IntegerProperty(default=0)
	exported_photos = ndb.IntegerProperty(default=0)
	created = ndb.DateTimeProperty(auto_now_add=True)
	updated = ndb.DateTimeProperty(auto_now=True)
	filename = ndb.StringProperty()
	status = ndb.StringProperty(choices=['new', 'inprogress', 'finished', 'failed'],default='new')
	message = ndb.TextProperty(default='Waiting for task to start...')

	def update(self, message, **kwargs):
		self.message = message
		for k,v in kwargs.items():
			self.__setattr__(k, v)
		self.put()
