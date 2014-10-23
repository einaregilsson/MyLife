from __future__ import with_statement
import webapp2, time, logging, json, zipfile, datetime, re, traceback
from StringIO import StringIO
from models.post import Post
from models.importtask import ImportTask
from models.userimage import UserImage
from models.postcounter import PostCounter
from google.appengine.ext import ndb, blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import taskqueue
from errorhandling import log_error

class UploadFinishedHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		upload = self.get_uploads()[0]
		task = ImportTask(
			blob_key = upload.key()
			)
		task.put()

		retry_options = taskqueue.TaskRetryOptions(task_retry_limit=0)
		queue_task = taskqueue.Task(url='/import', params={"task":task.key.urlsafe()}, retry_options=retry_options)
		queue_task.add()
		result = {"message" : "Upload finished, starting import...", "id" : task.key.urlsafe()}
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))


class ImportHandler(webapp2.RequestHandler):
	def post(self):

		import_task_key = ndb.Key(urlsafe=self.request.get('task'))
		import_task = import_task_key.get()

		import_task.update('Unpacking zip file...', status='inprogress')

		logging.info('Starting import ...')
		counter = PostCounter.get()
		try:


			posts, images = self.read_zip_file(import_task.blob_key)

			import_task.update('Importing...', total_photos=len(images), total_posts=len(posts))
			logging.info('Importing %s posts, %s images' % (len(posts), len(images)))

			posts = self.filter_posts(posts)
			
			for date, text in posts:
				str_date = date.strftime('%Y-%m-%d')

				p = Post(
					date=date,
					source='ohlife',
					text=text.decode('utf-8')
				)

				p.images = []
				p.has_images = False

				post_images = [(k,images[k]) for k in images.keys() if str_date in k]

				if len(post_images):
					logging.info('Importing %s images for date %s' % (len(post_images), str_date))
					p.images = []
					p.has_images = True
					for name, bytes in post_images:
						user_image = UserImage()
						img_name = name.replace('img_', '').replace('.jpeg', '.jpg')
						user_image.import_image(img_name, name, bytes, date)
						p.images.append(img_name)
						import_task.imported_photos += 1
						user_image.put()

				p.put()
				counter.increment(p.date.year, p.date.month, False)

				import_task.imported_posts += 1
				if import_task.imported_posts % 10 == 0:

					import_task.update('Imported %s/%s post, %s/%s photos...' % (import_task.imported_posts, import_task.total_posts,import_task.imported_photos, import_task.total_photos))
					logging.info(import_task.message)
					counter.put()

			counter.put()

			skipped_posts = import_task.total_posts - import_task.imported_posts
			skipped_photos = import_task.total_photos - import_task.imported_photos
			msg = 'Imported %s posts and %s photos.' % (import_task.imported_posts, import_task.imported_photos)
			if skipped_posts or skipped_photos:
				msg += ' %s posts and %s photos already existed and were skipped.' % (skipped_posts, skipped_photos)
			
			import_task.update(msg, status='finished')
			logging.info(import_task.message)
			blobstore.delete(import_task.blob_key)
		except Exception, ex:
			try:
				blobstore.delete(import_task.blob_key)
			except:
				pass
				
			try:
				counter.put()
			except:
				pass
			import_task.update('Failed to import: %s' % ex, status='failed')
			log_error('Failed import', traceback.format_exc(6))

	def read_zip_file(self, blob_key):
		blob_reader = blobstore.BlobReader(blob_key, buffer_size=1048576)
		zip_data = blob_reader.read()

		zip = zipfile.ZipFile(StringIO(zip_data))

		text = None
		images = {}

		for name in zip.namelist():
			if name.endswith('.txt'):
				text = zip.read(name)
			else:
				images[re.sub('^/', '', name)] = zip.read(name)
		

		text = text.replace('\r\n', '\n').strip()

		lines = text.split('\n')
		posts = []

		prev_line_empty = True
		current_date, current_text = None, ''
		for i,line in enumerate(lines):
			next_line_empty = i == len(lines)-1 or lines[i+1] == ''
			m = re.match(r'^(\d\d\d\d)-(\d\d)-(\d\d)$', line)
			
			if m and prev_line_empty and next_line_empty:
				if current_date:
					posts.append((current_date, current_text.rstrip()))
				current_text = ''
				current_date = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
			else:
				current_text += line + '\r\n'

			prev_line_empty = line == ''

		if current_text:
			posts.append((current_date, current_text.rstrip()))

		return posts, images

	def filter_posts(self, new_posts):
		#Lets check if we're going to overwrite anything...
		existing_posts = [p.date  for p in Post.query()]
		
		filtered_posts = []

		for date, text in new_posts:
			if date in existing_posts:
				logging.info('Skipping post for %s, already exists' % date)
 			else:
				filtered_posts.append((date,text))

		return filtered_posts

class ImportStatusHandler(webapp2.RequestHandler):
	def get(self, id):
		import_task = ndb.Key(urlsafe=id).get()

		result = {"status":import_task.status, "message" : import_task.message}
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps(result))

