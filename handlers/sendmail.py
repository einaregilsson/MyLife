import webapp2
from models.dailymail import DailyMail

class SendMailHandler(webapp2.RequestHandler):
	def get(self):

		DailyMail().send()