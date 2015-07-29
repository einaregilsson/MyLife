from __future__ import with_statement
import webapp2, time, logging, json, traceback
from models.migratetask import MigrateTask
from models.userimage import UserImage
from google.appengine.ext import ndb
from errorhandling import log_error
from google.appengine.api import taskqueue

class MigrateStartHandler(webapp2.RequestHandler):
	def post(self):

		task = MigrateTask()
		task.put()

		retry_options = taskqueue.TaskRetryOptions(task_retry_limit=0)
		queue_task = taskqueue.Task(url='/migrate/run', params={"task":task.key.urlsafe()}, retry_options=retry_options)
		queue_task.add()
		result = {"message" : "Migration queued and will start in a few seconds...", "id" : task.key.urlsafe()}
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))


class MigrateHandler(webapp2.RequestHandler):
	def post(self):

		task_key = ndb.Key(urlsafe=self.request.get('task'))
		task = task_key.get()

		task.update('Starting migration...', status='inprogress')

		logging.info('Starting migration ...')
		try:

			images = [i for i in UserImage.query() if i.filename != i.original_size_key]

			task.update('Migrating...', total_images=len(images))
			logging.info('Migrating %s images' % len(images))

			for img in images:
								
				img.migrate_to_gcs()
				task.migrated_images += 1
				if task.migrated_images % 3 == 0:
					task.update('Migrated %s/%s images' % (task.migrated_images, task.total_images))
					logging.info(task.message)
					task.put()


			
			task.update('Finished migrating images. Have a nice day :)', status='finished')
			logging.info(task.message)
		except Exception, ex:
			task.update('Failed to migrate: %s' % ex, status='failed')
			log_error('Failed migrate images', traceback.format_exc(6))

	
class MigrateStatusHandler(webapp2.RequestHandler):
	def get(self, id):
		task = ndb.Key(urlsafe=id).get()

		result = {"status":task.status, "message" : task.message}
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))

