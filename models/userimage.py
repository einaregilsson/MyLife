import datetime, logging, re
from google.appengine.ext import ndb, blobstore
from google.appengine.api import images, files


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

		return date.strftime('%Y-%m-%d-') + str(img_counter) + '.' + extension

	def import_image(self, filename, original_filename, bytes, date):

		ln = original_filename.lower()
		if ln.endswith('.jpg') or ln.endswith('.jpeg'):
			mime_type = 'image/jpg'
		elif ln.endswith('.png'):
			mime_type = 'image/png'
		elif ln.endswith('.gif'):
			mime_type = 'image/gif'
		elif ln.endswith('.bmp'):
			mime_type = 'image/bmp'
		else:
			raise Exception('Unexpected image type: %s' % original_filename)

		self.original_size_key = str(self._create_image(mime_type, bytes, original_filename))

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

		self.serving_size_key = str(self._create_image(mime_type, resized_bytes, filename))
		self.original_filename = original_filename
		self.filename = filename
		self.date = date
		

	def _create_image(self, mime_type, bytes, original_name):
		file_name = files.blobstore.create(mime_type=mime_type,_blobinfo_uploaded_filename=original_name)

		with files.open(file_name, 'a') as f:
 			f.write(bytes)

		files.finalize(file_name)

		return files.blobstore.get_blob_key(file_name)
