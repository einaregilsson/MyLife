import traceback
from google.appengine.api import mail
import datetime, uuid, re, logging, os
from models.slug import Slug
from models.post import Post
from models.settings import Settings
from models.timezones import timezones
from google.appengine.api import app_identity
from errorhandling import log_error

class DailyMail():
	
	def send(self, is_intro_email=False):

		try:
			now = datetime.datetime.now()
			settings = Settings.get()

			if is_intro_email:
				current_time = now
				logging.info('Sending intro email to %s' % settings.email_address)
			else:
				current_time, id, name, offset = self.get_time_in_timezone(settings)

				if current_time.hour != settings.email_hour:
					logging.info('Current time for %s is %s, not sending email now, will send at %02d:00' % (name, current_time, settings.email_hour))
					return


			today = current_time.date()
			
			if self.check_if_intro_email_sent_today(today):
				logging.info('Already sent the intro email today, skipping this email for now')	
				return	

			self.check_if_mail_already_sent(today)	


			slug_id = self.get_slug()

			slug = Slug(slug=slug_id, date=today)

			slug.put()

			subject = "It's %s, %s %s - How did your day go?" % (today.strftime('%A'), today.strftime("%b"), today.day)
			app_id = app_identity.get_application_id()

			sender = "MyLife <post+%s@%s.appspotmail.com>" % (slug.slug, app_id)

			message = mail.EmailMessage(sender=sender, subject=subject)

			message.to = settings.email_address
			if not settings.email_address:
				log_error('Missing To in daily email', 'There is no configured email address in your settings. Please visit your settings page to configure it so we can send you your daily email.')
				return

			message.body = """
Just reply to this email with your entry.

OLD_POST
You can see your past entries here:
https://APP_ID.appspot.com/past

	""".replace('APP_ID', app_id)

			message.html = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.=
w3.org/TR/html4/loose.dtd">
<html>
	<head>
		<title></title>
	</head>
	<body>
	Just reply to this email with your entry.
	<br>
	<br>
OLD_POST
	<a href="https://APP_ID.appspot.com/past">Past entries</a>
	</body>
</html>
""".replace('APP_ID', app_id)

			if is_intro_email:
				intro_msg = "Welcome to MyLife. We've sent you this email immediately so you can try the system out. In the future we will email you once a day and include an old post in each email. You can configure when you get your email and which email address we should use on the settings page."
				message.html = message.html.replace('OLD_POST', intro_msg + '<br><br>')
				message.body = message.body.replace('OLD_POST', intro_msg + '\r\n\r\n')
			else:
				#Lets try to put in an old post...
				old_post, old_type = self.get_old_post(today)

				if old_post and settings.include_old_post_in_entry:
					old_post_text = 'Remember this? One %s ago you wrote:\r\n\r\n' % old_type
					old_post_text += old_post.text.rstrip() + '\r\n\r\n'

					message.body = re.sub(r'OLD_POST\r?\n', old_post_text, message.body)

					old_post_text = re.sub(r'\r?\n', '<br>', old_post_text)
					message.html = re.sub(r'OLD_POST\r?\n', old_post_text, message.html)
				else:
					message.body = re.sub('OLD_POST\r?\n', '', message.body)
					message.html = re.sub('OLD_POST\r?\n', '', message.html)

			message.send()
			
			if is_intro_email:
				logging.info('Sent intro email')
			else:
				if old_post:
					logging.info('Sent daily email to %s, using old post from %s' % (message.to, old_post.date))
				else:
					logging.info('Sent daily email to %s, could not find old post' % message.to)

			return 'Email sent'
		except:
			log_error('Failed to send daily email', traceback.format_exc(6))
			return 'Failed sending email: %s' % traceback.format_exc(6)


	def get_time_in_timezone(self, settings):
		now = datetime.datetime.now()

		for id, name, offset in timezones:
			if id == settings.timezone:
				break

		local_timestamp = datetime.datetime.now() + datetime.timedelta(minutes=offset)	

		return local_timestamp, id, name, offset

	def get_slug(self):

		slug = str(uuid.uuid4())[0:13].replace('-', '')		

		# OK, this should never happen, but I'm not using the full uuid here
		# so lets just make sure...
		while Slug.query(Slug.slug == slug).get():
			slug = str(uuid.uuid4())[0:13].replace('-', '')		

		return slug

	def check_if_mail_already_sent(self, date):
		#Check if we've already sent an email
		existing_slug = Slug.query(Slug.date == date).get()

		if existing_slug:
			msg = 'Tried to send another email on %s, already sent %s' % (date, existing_slug.slug)
			log_error('Tried to send email again', msg)
			raise Exception(msg)

	def check_if_intro_email_sent_today(self, date):
		two_slugs = [s for s in Slug.query().fetch(2)]

		return len(two_slugs) == 1 and two_slugs[0].date == date

	def get_old_post(self, today):
		#Lets try to put in an old post...
		old_post = None
		old_type = ''

		#First try a year ago...
		if today.day == 29 and today.month == 2:
			old_post = None
		else:
			year_ago = datetime.date(today.year-1, today.month, today.day)
			old_post = Post.query(Post.date == year_ago).get()
			old_type = 'year'

		if not old_post:
			#lets try a month ago...
			last_day_of_last_month = datetime.date(today.year, today.month, 1) + datetime.timedelta(days=-1)
			if last_day_of_last_month.day >= today.day:
				month_ago = datetime.date(last_day_of_last_month.year, last_day_of_last_month.month, today.day)
				old_post = Post.query(Post.date == month_ago).get()
				old_type = 'month'

		if not old_post:
			week_ago = today + datetime.timedelta(days=-7)
			old_post = Post.query(Post.date == week_ago).get()
			old_type = 'week'

		if not old_post:
			return None, None
		else:
			return old_post, old_type


