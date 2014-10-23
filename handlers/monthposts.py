import webapp2, datetime, json, random
from templates import get_template
from models.post import Post
from models.postcounter import PostCounter

class MonthPostsHandler(webapp2.RequestHandler):
	def get(self, year, month):
		from = datetime.date(int(year), int(month), 1)

		posts = Post.query(Post.date < date).order(-Post.date).fetch(1)

		result = {
			"year" : year,
			"month" : month,
			"days" : [p.date.day for p in posts]
		}

		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))


