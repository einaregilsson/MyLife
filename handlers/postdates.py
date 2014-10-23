import webapp2, datetime, json
from models.post import Post
from google.appengine.ext import ndb


class PostDatesHandler(webapp2.RequestHandler):
	def get(self, year, month):
		year, month = int(year), int(month)
		from_date = datetime.date(int(year), int(month), 1)
		next_month = from_date + datetime.timedelta(days=33)

		to_date = datetime.date(next_month.year, next_month.month, 1)

		days = [p.date.day for p in Post.query(ndb.AND(Post.date >= from_date, Post.date < to_date)).order(-Post.date).fetch()]

		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps({"key" : from_date.strftime('%Y-%m'), "days": days}))

