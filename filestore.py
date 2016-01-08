import cloudstorage
from google.appengine.api import app_identity
from google.appengine.ext import blobstore


def _bucket_name():
	return app_identity.get_default_gcs_bucket_name()

def _path(filename):

	gcs_prefix = '/gs/'
	if filename.startswith(gcs_prefix):
		filename = filename[len(gcs_prefix)-1:]

	bucket_prefix = '/' + _bucket_name() + '/'

	if filename.startswith(bucket_prefix):
		filename = filename[len(bucket_prefix):]

	return '/%s/%s' % (_bucket_name(), filename)

def read(filename):
	return cloudstorage.open(_path(filename)).read()

def write(filename, bytes, content_type=None):
	with cloudstorage.open(_path(filename), 'w', content_type=content_type) as f:
		f.write(bytes)

def delete(filename):
	cloudstorage.delete(_path(filename))

def exists(filename):
	pass

def get_blob_key(filename):
	return blobstore.create_gs_key('/gs' + _path(filename))

def create_upload_url(path):
	return blobstore.create_upload_url(path, gs_bucket_name=_bucket_name())

def bucket_exists():
	return bool(_bucket_name())