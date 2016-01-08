from __future__ import with_statement
import webapp2, time, zipfile, re, datetime, logging, json, filestore
from StringIO import StringIO
from models.post import Post
from models.userimage import UserImage
from models.exporttask import ExportTask
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import taskqueue

class ExportStartHandler(webapp2.RequestHandler):
	def post(self):
		task = ExportTask()
		task.put()

		retry_options = taskqueue.TaskRetryOptions(task_retry_limit=0)
		queue_task = taskqueue.Task(url='/export/run', params={"task":task.key.urlsafe()}, retry_options=retry_options)
		queue_task.add()
		result = {"message" : "Waiting for task to start..", "id" : task.key.urlsafe()}
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))


class ExportHandler(webapp2.RequestHandler):
	def post(self):

		export_task_key = ndb.Key(urlsafe=self.request.get('task'))
		export_task = export_task_key.get()
		try:
			day_string = datetime.datetime.today().strftime('%Y-%m-%d')
			zip_filename = 'export_%s.zip' % day_string
			logging.info('Starting export task')

			self.cleanup_old_export_tasks()

			buffer = StringIO()
			archive = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)

			self.add_posts_to_zip(export_task, archive, day_string)
			self.add_images_to_zip(export_task, archive)

			archive.close()
			
			export_task.update('Saving zip file...')
			self.create_zip_blob(buffer, zip_filename)

			export_task.update('Finished creating zip', status='finished', filename=zip_filename)

			self.enqueue_for_deletion(export_task)

		except Exception, ex:

			export_task.update('Failed to export: %s' % ex, status='failed')
		
			logging.error('Failed export: %s' % ex.message)


	def add_posts_to_zip(self, export_task, archive, day_string):

		export_task.update('Fetching posts...', status='inprogress')

		posts = [p for p in Post.query().order(Post.date).fetch()]

		export_task.update('Got %s posts, adding to zip...' % len(posts))
		post_text = ''
		for p in Post.query().order(Post.date).fetch():
			post_text += p.date.strftime('%Y-%m-%d')
			post_text += '\r\n\r\n'
			post_text += p.text.replace('\r\n', '\n').replace('\n', '\r\n').strip()
			post_text += '\r\n\r\n'

		archive.writestr('/export_%s.txt' % day_string, post_text.encode('utf-8'))

		export_task.update('Added %s posts to zip...' % len(posts))

	def enqueue_for_deletion(self, export_task):
		#Enqueue the task to be deleted in 15 minutes...
		timestamp = datetime.datetime.now() + datetime.timedelta(minutes=15)

		retry_options = taskqueue.TaskRetryOptions(task_retry_limit=0)
		queue_task = taskqueue.Task(url='/export/delete', eta=timestamp, params={"task":export_task.key.urlsafe()}, retry_options=retry_options)
		queue_task.add()		

	def cleanup_old_export_tasks(self):
		#Lets delete any old export tasks hanging around...
		old_deleted = 0
		for ex in ExportTask.query().fetch():
			if ex.status in ('finished', 'failed'):
				try:
					filestore.delete(ex.filename)
				except:
					pass
				ex.key.delete()
				old_deleted += 1

		if old_deleted > 0:
			logging.info('Deleted %s old export tasks' % old_deleted)


	def add_images_to_zip(self, export_task, archive):
		export_task.update('Fetching image information...')

		images = [i for i in UserImage.query().order(UserImage.filename).fetch()]

		export_task.update('Found %s images...' % len(images))

		for i, img in enumerate(images):
			img_data = filestore.read(img.original_size_key)
			archive.writestr('/img_%s' % img.filename.replace('.jpg', '.jpeg'), img_data)
			if i % 5 == 0:
				export_task.update('Added %s of %s images to zip... ' % (i+1,len(images)))

		export_task.update('Finished adding images...')

	def create_zip_blob(self, buffer, filename):
		filestore.write(filename, buffer.getvalue(), content_type='application/zip')

class ExportStatusHandler(webapp2.RequestHandler):
	def get(self, id):
		export_task = ndb.Key(urlsafe=id).get()

		result = {"status":export_task.status, "message" : export_task.message, "filename" : export_task.filename}
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))

class ExportDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, filename):

    	export = ExportTask.query(UserImage.filename == filename).get()
    	

        if not export:
            self.error(404)
        else:
			self.send_blob(filestore.get_blob_key(export.filename))

class ExportDeleteHandler(webapp2.RequestHandler):
	def post(self):
		export_task_key = ndb.Key(urlsafe=self.request.get('task'))
		export_task = export_task_key.get()

		if not export_task:
			logging.info('Export task already deleted')
			return

		try:
			filestore.delete(export_task.filename)
		except:
			logging.info('Failed to delete export blob')
		
		export_task.key.delete()
		logging.info('Deleted export task')
