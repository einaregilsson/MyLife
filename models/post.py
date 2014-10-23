import datetime
from google.appengine.ext import ndb


class Post(ndb.Model):
	text = ndb.TextProperty()
	date = ndb.DateProperty()
	source = ndb.StringProperty(choices=['empty', 'ohlife','email','web','mixed'], default='empty')
	created = ndb.DateTimeProperty(auto_now_add=True)
	updated = ndb.DateTimeProperty(auto_now=True)
	images=ndb.StringProperty(repeated=True)
	has_images = ndb.BooleanProperty(default=False)

	seperator = '-------------------------'
	
	def date_string(self):
		return self.date.strftime('%Y-%m-%d')

	@classmethod
	def min_date(cls):
		post = Post.query().order(Post.date).get()
		if post:
			return post.date
		return None

	@classmethod
	def max_date(cls):
		post = Post.query().order(-Post.date).get()
		if post:
			return post.date
		return None		