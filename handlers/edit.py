import webapp2, datetime, logging, json, filestore
from templates import get_template
from models.post import Post
from models.postcounter import PostCounter
from models.userimage import UserImage
from models.rawmail import RawMail
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import app_identity

	
class GetPhotoUploadUrlHandler(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(json.dumps({"upload_url" : filestore.create_upload_url('/api/addphoto')}))

class AddPhotoHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		file_info = self.get_file_infos()[0]
		self.response.headers['Content-Type'] = "application/json"
		year = self.request.get('year')
		month = self.request.get('month')
		day = self.request.get('day')
		date = datetime.datetime(int(year), int(month), int(day))

		if file_info.content_type.lower() not in ('image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp'):
			return self.response.write(json.dumps({"status" : "error", "message" : "Unsupported content type: " + file_info.content_type}))

		bytes = filestore.read(file_info.gs_object_name)
		existing_images = [u.filename for u in UserImage.query(UserImage.date == date).fetch()]

		filename = UserImage.create_image_name(file_info.filename, date, existing_images)
		img = UserImage()
		img.import_image(filename, file_info.filename, bytes, date)
		img.put()
		filestore.delete(file_info.gs_object_name)
		#If there's a post here we should add the image...
		post = Post.query(Post.date == date).get()
		if post:
			post.has_images = True
			if post.images is None:
				post.images = []
			post.images.append(filename)
			post.put()

		self.response.write(json.dumps({"status" : "ok", "filename" : filename}))

class DeletePhotoHandler(webapp2.RequestHandler):
	def post(self, filename):
		self.response.headers['Content-Type'] = "application/json"
		img = UserImage.query(UserImage.filename == filename).get()
		if not img:
			return self.response.write(json.dumps({"status" : "error", "message" : "Image does not exit"}))

		post = Post.query(Post.date == img.date).get()
		
		#Remove it from the post
		if post:
			try:
				post.images.remove(filename)
			except:
				pass

			if len(post.images) == 0:
				post.has_images = False

			post.put()

		filestore.delete(img.serving_size_key)
		filestore.delete(img.original_size_key)
		img.key.delete()

		self.response.write(json.dumps({"status" : "ok"}))

class EditHandler(webapp2.RequestHandler):
	def get(self, kind, year, month, day):
		date = datetime.datetime(int(year),int(month),int(day)).date()
		
		post = Post.query(Post.date == date).get()
		if kind == 'write' and post:
			return self.redirect('/edit/%s' % date.strftime('%Y-%m-%d'))
		if kind == 'edit' and not post:
			return self.redirect('/write/%s' % date.strftime('%Y-%m-%d'))
		
		data = { 
			"date" : date,
			"text" : "",
			"page" : "write",
			"kind" : kind
		}
		if post:
			data["page"] = "edit"
			data["text"] = post.text
			data["images"] = post.images
		else:
			data["images"] = [u.filename for u in UserImage.query(UserImage.date == date).fetch()]

		self.response.write(get_template('edit.html').render(data))

	def post(self, kind, year, month, day):
		date = datetime.datetime(int(year),int(month),int(day)).date()		
		post = Post.query(Post.date == date).get()
		
		is_new = False
		if not post:
			post = Post(date=date, source='web',images=[])
			is_new = True
		
		post.text = self.request.get('text')

		save = self.request.get('action') == 'save'
		delete = self.request.get('action') == 'delete'

		if save and delete:
			raise Exception('Something weird happened...')

		if save:
			if is_new:
				post.images = [u.filename for u in UserImage.query(UserImage.date == date).fetch()]
				post.images.sort()
				post.has_images = True

			post.put()
			if is_new:
				PostCounter.get().increment(post.date.year, post.date.month)

			self.redirect_to_date(post.date)
		elif delete:
			self.delete_post(post)

			next_post = Post.query(Post.date > date).order(Post.date).get()
			if next_post and next_post.date.month == date.month:
				return self.redirect_to_date(next_post.date)			

			#No way, we'll have to just redirect to the empty month
			self.redirect('/past/%s' % date.strftime('%Y-%m'))
		else:
			raise Exception('How the hell did we get here...?')

	def delete_post(self, post):
		images = UserImage.query(UserImage.date == post.date).fetch()

		for img in images:
			filestore.delete(img.serving_size_key)
			filestore.delete(img.original_size_key)
			img.key.delete()

		emails = RawMail.query(RawMail.date == post.date).fetch()
		for email in emails:
			email.key.delete()

		post.key.delete()
		PostCounter.get().decrement(post.date.year, post.date.month)
		
		logging.info('Deleted %s images, %s emails and 1 post from %s' % (len(images), len(emails), post.date.strftime('%Y-%m-%d')))
		
	def redirect_to_date(self, date):
		self.redirect('/past/%s#day-%s' % (date.strftime('%Y-%m'), date.day))