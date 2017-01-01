import traceback, random
from google.appengine.api import mail
import datetime, uuid, re, logging, os
from models.slug import Slug
from models.post import Post
from models.settings import Settings
from models.timezones import timezones
from models.postcounter import PostCounter
from google.appengine.api import app_identity
from errorhandling import log_error

class DailyMail():
	
	def send(self, is_intro_email=False, force_send=False, date=None):

		try:
			now = datetime.datetime.now()
			settings = Settings.get()

			if is_intro_email:
				current_time = now
				logging.info('Sending intro email to %s' % settings.email_address)
			else:
				current_time, id, name, offset = self.get_time_in_timezone(settings)

				if current_time.hour != settings.email_hour and not force_send:
					logging.info('Current time for %s is %s, not sending email now, will send at %02d:00' % (name, current_time, settings.email_hour))
					return


			if date and force_send:
				today = date #Allow overriding this stuff
			else:
				today = current_time.date()
			
			if self.check_if_intro_email_sent_today(today) and not force_send:
				logging.info('Already sent the intro email today, skipping this email for now')	
				return	


			#Check if we've already sent an email
			slug = Slug.query(Slug.date == today).get()

			if slug and not force_send:
				msg = 'Tried to send another email on %s, already sent %s' % (date, slug.slug)
				log_error('Tried to send email again', msg)
				raise Exception(msg)

			if not slug:
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
					logging.info('Going to use old post %s because %s' % (old_post, settings.include_old_post_in_entry))

					if (old_type == 'random'):
						old_post_text = 'Remember this? On %s you wrote:\r\n\r\n' % old_post.date
					else:
						old_post_text = 'Remember this? One %s ago you wrote:\r\n\r\n' % old_type
					old_post_text += old_post.text.rstrip() + '\r\n\r\n'

					message.body = re.sub(r'OLD_POST\r?\n', old_post_text, message.body)

					old_post_text = re.sub(r'\r?\n', '<br>', old_post_text)
					message.html = re.sub(r'OLD_POST\r?\n', old_post_text, message.html)
				else:
					logging.info('Not using Old post %s because %s' % (old_post, settings.include_old_post_in_entry))
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
			# lets try a week ago
			week_ago = today + datetime.timedelta(days=-7)
			old_post = Post.query(Post.date == week_ago).get()
			old_type = 'week'

		if not old_post:
			# lets try a completely random post
			count = PostCounter.get().count
			old_list = Post.query().fetch(1, offset=random.randint(0, count-1))
			old_post = old_list[0]
			old_type = 'random'


		if not old_post:
			logging.info('Looked for but didnt find old_post %s' % (old_post))
			return None, None
		else:
			logging.info('Found and returning old_post')
			return old_post, old_type


