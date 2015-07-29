import datetime, logging, re, filestore
from google.appengine.ext import ndb, blobstore
from google.appengine.api import images

class UserImage(ndb.Model):
	original_size_key = ndb.StringProperty()
	serving_size_key = ndb.StringProperty()
	original_filename = ndb.StringProperty()
	filename = ndb.StringProperty()
	date = ndb.DateProperty()
	created = ndb.DateTimeProperty(auto_now_add=True)
	backed_up_in_dropbox = ndb.BooleanProperty(required=False, default=False)

	@classmethod
	def create_image_name(cls, original_filename, date, existing_images):

		if len(existing_images) == 0:
			img_counter = 0
		else:
			img_counter = max([int(re.search(r'-(\d+)\.', i).group(1)) for i in existing_images]) + 1
		
		if not re.search('\\.(jpe?g|png|bmp|gif)$', original_filename.lower()):
			raise Exception('Unsupported filename: ' + original_filename)

		extension = original_filename.lower().split('.')[-1].replace('jpeg', 'jpg')

		name = date.strftime('%Y-%m-%d-') + str(img_counter) 
		return name + '.' + extension


	def migrate_to_gcs(self):
		if self.original_size_key == self.filename:
			raise Exception('This image (%s) looks like it already is in GCS' % self.filename)

		content_type = self.get_content_type(self.filename)

		image_bytes = blobstore.BlobReader(self.original_size_key, buffer_size=1048576).read()
		small_image_bytes = blobstore.BlobReader(self.serving_size_key, buffer_size=1048576).read()

		self.original_size_key = self.filename
		self.serving_size_key = self.get_small_image_name(self.filename)

		filestore.write(self.original_size_key, image_bytes, content_type)
		filestore.write(self.serving_size_key, small_image_bytes, content_type)

		self.put()

	def get_content_type(self, filename):

		ln = filename.lower()
		if ln.endswith('.jpg') or ln.endswith('.jpeg'):
			return 'image/jpg'
		elif ln.endswith('.png'):
			return 'image/png'
		elif ln.endswith('.gif'):
			return 'image/gif'
		elif ln.endswith('.bmp'):
			return 'image/bmp'
		else:
			raise Exception('Unexpected image type: %s' % filename)

	def get_small_image_name(self, filename):
		return filename[:-4] + '-small' + filename[-4:]

	def import_image(self, filename, original_filename, bytes, date):

		content_type = self.get_content_type(original_filename)
		self.original_size_key = filename
		filestore.write(self.original_size_key, bytes, content_type)

		MAX_SIZE = 500
		image = images.Image(bytes)

		if image.width <= MAX_SIZE and image.width <= MAX_SIZE:
			logging.info('%s is only %sx%s, no resizing will be done' % (original_filename, image.width, image.height))
			resized_bytes = bytes
		else:
			if image.width > image.height:
				new_width = MAX_SIZE
				new_height = int(float(MAX_SIZE) / image.width * image.height)
			else:
				new_height = MAX_SIZE
				new_width = int(float(MAX_SIZE) / image.height * image.width)

			logging.info('Resizing %s from %sx%s to %sx%s' % (original_filename, image.width, image.height, new_width, new_height))
			resized_bytes = images.resize(bytes, MAX_SIZE, MAX_SIZE)


		self.serving_size_key = self.get_small_image_name(filename)
		filestore.write(self.serving_size_key, resized_bytes, content_type)
		self.original_filename = original_filename
		self.filename = filename
		self.date = date
