import webapp2, filestore
from templates import get_template
from models.settings import Settings
from models.timezones import timezones
from models.migratetask import MigrateTask

class SettingsHandler(webapp2.RequestHandler):
	def get(self):
		self._render(Settings.get())

	def post(self):
		settings = Settings.get()

		settings.email_address = self.request.get('email-address')
		settings.timezone = self.request.get('timezone')
		settings.email_hour = int(self.request.get('email-hour'))
		settings.dropbox_access_token = self.request.get('dropbox-access-token')
		settings.include_old_post_in_entry = self.request.get('include-old-entry') == 'yes'
		settings.put()
		self._render(settings, True)

	def _render(self, settings, saved=False):
		data = {
			"page" : "settings",
			"email_address" : settings.email_address,
			"dropbox_access_token" : settings.dropbox_access_token or "",
			"timezone" : settings.timezone,
			"timezones" : timezones,
			"email_hour" : settings.email_hour,
			"include_old_post_in_entry" : settings.include_old_post_in_entry,
			"upload_url" : filestore.create_upload_url('/upload-finished'),
			"saved" : saved,
			"can_migrate_images" : not bool(MigrateTask.query(MigrateTask.status == 'finished').get())
		}
		self.response.write(get_template('settings.html').render(data))
