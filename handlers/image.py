from google.appengine.ext.webapp import blobstore_handlers
import filestore
from models.userimage import UserImage

class ImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, filename):

        image = UserImage.query(UserImage.filename == filename).get()

        if self.request.get('fullsize'):
            key = image.original_size_key
        else:
            key = image.serving_size_key

        if not image:
            self.error(404)
        else:
            self.send_blob(filestore.get_blob_key(key))

