import webapp2, datetime, logging
from templates import get_template
from models.post import Post
from models.postcounter import PostCounter, Month
from google.appengine.ext import ndb
from models.settings import Settings

class PastHandler(webapp2.RequestHandler):
	def get(self, year, month):
		Settings.get() #Force email address update...

		now = datetime.datetime.now()
		if not year:
			last_post = Post.query().order(-Post.date).get()
			if last_post:
				year, month = last_post.date.year, last_post.date.month
			else:
				year, month = now.year, now.month
		else:
			year, month = int(year), int(month)

		from_date = datetime.date(year, month, 1)
		
		to_month = month + 1
		to_year = year
		if to_month == 13:
			to_month = 1
			to_year += 1

		to_date = datetime.date(to_year, to_month, 1)
		posts = [p for p in Post.query(ndb.AND(Post.date >= from_date, Post.date < to_date)).order(-Post.date).fetch()]
		month_name = from_date.strftime('%B %Y')
		
		#Get month list
		months = PostCounter.get().months[:]
		def cmp_months(a,b):
			if a.year != b.year:
				return cmp(a.year, b.year)
			else:
				return cmp(a.month, b.month)

		months.sort(cmp_months)

		archive = []

		next_link, prev_link = None, None

		for i, m in enumerate(months):
			date = datetime.date(m.year, m.month,1)
			descr = '%s, %s posts' % (date.strftime('%B %Y'), m.count)
			value = date.strftime('%Y-%m')
			archive.append((value,descr, m.year == year and m.month == month))
			if m.year == year and m.month == month:
				if i != 0:
					prev_link = '/past/%s' % datetime.date(months[i-1].year, months[i-1].month, 1).strftime('%Y-%m')

				if i < len(months)-1:
					next_link = '/past/%s' % datetime.date(months[i+1].year, months[i+1].month, 1).strftime('%Y-%m')

		if not archive:
			archive.append(('', '%s, 0 posts' % now.strftime('%B %Y'), False))

		data = {
			"page" : "past", 
			"posts" : posts, 
			"month" : month_name,
			"archive" : archive,
			"next" : next_link,
			"prev" : prev_link
		}
		self.response.write(get_template('past.html').render(data))
