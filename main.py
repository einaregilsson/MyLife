#!/usr/bin/env python
import webapp2, logging
from templates import get_template

from handlers.calendar import CalendarHandler
from handlers.dataupgrade import DataUpgradeHandler
from handlers.dropbox import DropboxBackupHandler
from handlers.edit import EditHandler, AddPhotoHandler, GetPhotoUploadUrlHandler, DeletePhotoHandler
from handlers.export import ExportHandler, ExportDeleteHandler, ExportDownloadHandler, ExportStartHandler, ExportStatusHandler
from handlers.frontpage import FrontPageHandler, FrontPagePostHandler
from handlers.image import ImageHandler
from handlers.past import PastHandler
from handlers.postdates import PostDatesHandler
from handlers.receivemail import ReceiveMailHandler
from handlers.sendmail import SendMailHandler
from handlers.settings import SettingsHandler
from handlers.upload import UploadFinishedHandler, ImportHandler, ImportStatusHandler


app = webapp2.WSGIApplication([
	(r'/', FrontPageHandler),
	(r'/api/addphoto', AddPhotoHandler),
	(r'/api/photouploadurl', GetPhotoUploadUrlHandler),
	(r'/api/(\d\d\d\d)-(\d\d)-(\d\d)/(next|prev|random)', FrontPagePostHandler),
	(r'/write', CalendarHandler),
	(r'/dataupgrade', DataUpgradeHandler),
	(r'/backup/dropbox', DropboxBackupHandler),
	(r'/(edit|write)/(\d\d\d\d)-(\d\d)-(\d\d)', EditHandler),
	(r'/export/delete', ExportDeleteHandler),
	(r'/export/download/(.*)', ExportDownloadHandler),
	(r'/export/run', ExportHandler),
	(r'/export/start', ExportStartHandler),
	(r'/export/status/(.*)', ExportStatusHandler),
	(r'/image/delete/(.*)', DeletePhotoHandler),
	(r'/image/(.*)', ImageHandler),
	(r'/import', ImportHandler),
	(r'/import/status/(.*)', ImportStatusHandler),
	(r'/past(?:/(\d\d\d\d)-(\d\d))?', PastHandler),
	(r'/postdates/(\d\d\d\d)-(\d\d)', PostDatesHandler),
	(r'/sendmail', SendMailHandler),
	(r'/settings', SettingsHandler),
	(r'/upload-finished', UploadFinishedHandler),
	ReceiveMailHandler.mapping()
], debug=True)

