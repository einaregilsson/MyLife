from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.runtime import apiproxy_errors
from google.appengine.ext import ndb
from models.rawmail import RawMail
from models.post import Post
from models.settings import Settings
from models.userimage import UserImage
from models.slug import Slug
from models.userimage import UserImage
from models.postcounter import PostCounter
import re, logging, exceptions, traceback, webapp2, json, datetime, filestore
from errorhandling import log_error
from google.appengine.api import urlfetch
from StringIO import StringIO

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


			posts = [p for p in Post.query().order(Post.date).fetch()]

			self.log('Backing up %s posts to Dropbox' % len(posts))
			post_text = StringIO()
			for p in posts:
				post_text.write(p.date.strftime('%Y-%m-%d'))
				post_text.write('\r\n\r\n')
				post_text.write(p.text.replace('\r\n', '\n').replace('\n', '\r\n').rstrip())
				post_text.write('\r\n\r\n')

			result = self.put_file(settings.dropbox_access_token, 'MyLife.txt', post_text.getvalue().encode('utf-8'))
			post_text.close()
			self.log('Backed up posts. Revision: %s' % result['rev'])

			self.log('Fetching Dropbox file list')
			
			files_in_dropbox = self.get_dropbox_filelist(settings.dropbox_access_token)
			
			self.log('Got %s files from Dropbox' % len(files_in_dropbox))

			self.log('Fetching images...')
			images = [i for i in UserImage.query().order(UserImage.date).fetch()]

			self.log('Total images in MyLife: %s' % len(images))

			not_backed_up = [i for i in images if not i.backed_up_in_dropbox]
			not_in_dropbox = [i for i in images if not i.filename in files_in_dropbox]

			self.log('\nFiles not backed up: \n\n' + '\n'.join([i.filename for i in not_backed_up]))
			self.log('\nFiles marked as backed up, but not in Dropbox: \n\n' + '\n'.join([i.filename for i in not_in_dropbox]))

			images = not_backed_up + not_in_dropbox

			images_total = len(images)
			self.log('Found %s images that need to be backed up in Dropbox' % images_total)
			for img in images:
				self.log('Backing up %s' % img.filename)
				bytes = filestore.read(img.original_size_key)
				result = self.put_file(settings.dropbox_access_token, img.filename, bytes)
				self.log('Backed up %s. Revision: %s' % (img.filename, result['rev']))
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
			self.log('Failed to backup posts and images to dropbox: %s' % traceback.format_exc(6))
			logging.exception("message")
			self.log('ERROR: %s' % ex)
			log_error('Error backing up to Dropbox', 'Failed to backup posts and images to dropbox: %s' % traceback.format_exc(6))


	def log(self, msg):
		self.response.write(str(msg) + '\r\n')
		logging.info(msg)

	def get_file_info(self, access_token, name):

		headers = {
			'Content-Type' : 'application/json',
			'Authorization' : 'Bearer ' + access_token
		}

		data = {
    		"path": "/" + name,
		    "include_media_info": False,
		    "include_deleted": False,
		    "include_has_explicit_shared_members": False
		}

		result = urlfetch.fetch(
			payload=json.dumps(data),
			method=urlfetch.POST,
			url='https://api.dropboxapi.com/2/files/get_metadata',
			headers=headers
		)

		if result.status_code != 200:
			raise Exception("Failed to get file metadata from Dropbox. Status: %s, body: %s" % (result.status_code, result.content))
		self.log(result.content)
		return json.loads(result.content)


	def put_file(self, access_token, name, bytes):

#		info = self.get_file_info(access_token, name)
#		self.log(info)

		dropbox_args = {
    		"path": "/" + name,
    		"mode": { ".tag" : "overwrite"},
    		"autorename": True,
    		"mute": False
		}

		headers = {
			'Content-Type' : 'application/octet-stream',
			'Authorization' : 'Bearer ' + access_token,
			'Dropbox-API-Arg' : json.dumps(dropbox_args)
		}

		result = urlfetch.fetch(
			payload=bytes,
			method=urlfetch.POST,
			url='https://content.dropboxapi.com/2/files/upload',
			headers=headers
		)

		if result.status_code != 200:
			self.log(result.content)
			raise Exception("Failed to send file to Dropbox. Status: %s, body: %s" % (result.status_code, result.content))
		return json.loads(result.content)


	def get_dropbox_filelist(self, access_token):
		headers = {
			'Content-Type' : 'application/json',
			'Authorization' : 'Bearer ' + access_token
		}

		data = {
			"path": "",
			"recursive": True,
			"include_media_info": False,
			"include_deleted": False,
			"include_has_explicit_shared_members": False,
			"include_mounted_folders": False,
			"limit" : 1000
		}

		result = urlfetch.fetch(
			payload=json.dumps(data),
			method=urlfetch.POST,			
			url='https://api.dropboxapi.com/2/files/list_folder',
    		headers=headers)

		if result.status_code != 200:
			raise Exception("Failed to get files from Dropbox. Status: %s, body: %s" % (result.status_code, result.content))
		
		json_data = json.loads(result.content)
		file_list = [o['name'] for o in json_data['entries']]

		#Get everything
		while json_data['has_more']:
			self.log('Getting next batch...')
			result = urlfetch.fetch(
				payload=json.dumps({"cursor" : json_data['cursor']}),
				method=urlfetch.POST,			
				url='https://api.dropboxapi.com/2/files/list_folder/continue',
	    		headers=headers)

			if result.status_code != 200:
				raise Exception("Failed to get files from Dropbox. Status: %s, body: %s" % (result.status_code, result.content))

			json_data = json.loads(result.content)
			file_list.extend([o['name'] for o in json_data['entries']])

		return file_list	

