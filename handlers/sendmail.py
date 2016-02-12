import webapp2, datetime
from models.dailymail import DailyMail

class SendMailHandler(webapp2.RequestHandler):
	def get(self):

		force = self.request.get('force', '0') == '1'
		date = self.request.get('date', None)
		if date:
			try:
				y,m,d = date.split('-')
				date = datetime.datetime(int(y), int(m), int(d)).date()
			except:
				self.response.out.write('Invalid date, ignored')

		DailyMail().send(False, force, date)
		self.response.out.write('Ran daily mail at ' + str(datetime.datetime.now()))