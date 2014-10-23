import logging
from google.appengine.api import mail
from google.appengine.api import app_identity
from models.settings import Settings

def log_error(subject, message, *args):
	if args:
		try:
			message = message % args
		except:
			pass

	logging.error(subject + ' : ' + message)

	subject = 'MyLife Error: ' + subject
	app_id = app_identity.get_application_id()
	sender = "MyLife Errors <errors@%s.appspotmail.com>" % app_id
	try:
		to = Settings.get().email_address
		mail.check_email_valid(to, 'To')
		mail.send_mail(sender, to, subject, message)
	except:
		mail.send_mail_to_admins(sender, subject, message)


