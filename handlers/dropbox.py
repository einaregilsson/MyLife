from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.runtime import apiproxy_errors
from google.appengine.ext import ndb, blobstore
from models.rawmail import RawMail
from models.post import Post
from models.settings import Settings
from models.userimage import UserImage
from models.slug import Slug
from models.userimage import UserImage
from models.postcounter import PostCounter
import re, logging, exceptions, traceback, webapp2, json, datetime
from errorhandling import log_error
from google.appengine.api import urlfetch

class DropboxBackupHandler(webapp2.RequestHandler):
	def get(self):
		images_total = 0
		images_backed_up = 0
		try:
			self.response.headers['Content-Type'] = 'text/plain'
			settings = Settings.get()

			if not settings.dropbox_access_token:
				self.log('No access token available, no backup will be performed.')
				return

			headers = {
				'Content-Type' : 'application/json',
				'Authorization' : 'Bearer ' + settings.dropbox_access_token
			}

			posts = [p for p in Post.query().order(Post.date).fetch()]

			self.log('Backing up %s posts to Dropbox' % len(posts))
			post_text = ''
			for p in posts:
				post_text += p.date.strftime('%Y-%m-%d')
				post_text += '\r\n\r\n'
				post_text += p.text.replace('\r\n', '\n').replace('\n', '\r\n').rstrip()
				post_text += '\r\n\r\n'

			result = self.put_file(headers, 'MyLife.txt', post_text.encode('utf-8'))
			self.log('Backed up posts. Revision: %s' % result['revision'])

			result = self.get_dropbox_filelist(settings.dropbox_access_token, headers)

			self.log('Fetching Dropbox file list')
			
			files_in_dropbox = [m['path'][1:] for m in result['contents']]
			
			self.log('Fetching images...')
			images = [i for i in UserImage.query().order(UserImage.date).fetch()]

			images = [i for i in images if not i.filename in files_in_dropbox or not i.backed_up_in_dropbox]

			images_total = len(images)
			self.log('Found %s images that need to be backed up in Dropbox' % images_total)
			for img in images:
				self.log('Backing up %s' % img.filename)
				bytes = blobstore.BlobReader(img.original_size_key, buffer_size=1048576).read()
				result = self.put_file(headers, img.filename, bytes)
				self.log('Backed up %s. Revision: %s' % (img.filename, result['revision']))
				img.backed_up_in_dropbox = True
				img.put()
				images_backed_up += 1


			settings.dropbox_last_backup = datetime.datetime.now()
			settings.put()
			self.log('Finished backup successfully')
		except apiproxy_errors.OverQuotaError, ex:
			self.log(ex)
			log_error('Error backing up to Dropbox, quota exceeded', 'The backup operation did not complete because it ran out of quota. ' +
				'The next time it runs it will continue backing up your posts and images.' +
				'%s images out of %s were backed up before failing' % (images_backed_up, images_total))
		except Exception, ex:
			self.log('ERROR: %s' % ex)
			log_error('Error backing up to Dropbox', 'Failed to backup posts and images to dropbox: %s' % traceback.format_exc(6))


	def log(self, msg):
		self.response.write(str(msg) + '\r\n')
		logging.info(msg)

	def put_file(self, headers, name, bytes):

		params = {

		}

		qs = '&'.join('%s=%s' % (k,v) for k,v in params.items())

		result = urlfetch.fetch(
			payload=bytes,
			method=urlfetch.POST,
			url='https://api-content.dropbox.com/1/files_put/auto/' + name + '?' + qs,
			headers=headers
			)
		if result.status_code != 200:
			raise Exception("Failed to send file to Dropbox. Status: %s, body: %s" % (result.status_code, result.content))
		return json.loads(result.content)


	def get_dropbox_filelist(self, access_token, headers):
		result = urlfetch.fetch(
			url='https://api.dropbox.com/1/metadata/auto/',
    		headers=headers)
		if result.status_code != 200:
			raise Exception("Failed to send file to Dropbox. Status: %s, body: %s" % (result.status_code, result.content))
		
		return json.loads(result.content)		

