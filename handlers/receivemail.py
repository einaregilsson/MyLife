from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from models.rawmail import RawMail
from models.post import Post
from models.slug import Slug
from models.userimage import UserImage
from models.postcounter import PostCounter
import re, logging, exceptions, traceback
from errorhandling import log_error

def strip_html(text):
    def fixup(m):
        text = m.group(0)
        if text == '<br>' or text == '<br/>':
        	return '\r\n'
        if text[:1] == "<":
            return "" # ignore tags
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        elif text[:1] == "&":
            import htmlentitydefs
            entity = htmlentitydefs.entitydefs.get(text[1:-1])
            if entity:
                if entity[:2] == "&#":
                    try:
                        return unichr(int(entity[2:-1]))
                    except ValueError:
                        pass
                else:
                    return unicode(entity, "latin-1")
        
        return text # leave as is
    
    #OK, first lets see if we have any images in the html...

    image_tags = re.findall('<img[^>]*>', text)
    for tag in image_tags:
    	match = re.search('\\bcid:(\\w+)', tag)
    	if match:
    		content_id = match.group(1)
    		text = text.replace(tag, '\r\n\r\n$IMG:' + content_id + '\r\n\r\n') #These can then be replaced later...


    return re.sub("(?s)<[^>]*>|&#?\w+;", fixup, text)

class ReceiveMailHandler(InboundMailHandler):
	
	def receive(self, mail_message):

		try:
			id = self.get_id(mail_message)

			if not id: 
				return
			
			slug = Slug.query(Slug.slug == id).get()

			if not slug:
				log_error('Invalid slug', 'Found no slug for id %s', id)
				return

			body_text, body_html = self.get_bodies(mail_message)

			raw_mail = RawMail(
				subject=mail_message.subject,
				sender=mail_message.sender,
				slug=id,
				date=slug.date,
				text=body_text,
				html=body_html
				)

			raw_mail.put()

			post = Post.query(Post.date == slug.date).get()
			is_new_post = post is None
			if is_new_post:
				post = Post(
					date=slug.date,
					source='email',
					has_images=False
				)

			#Now let's try parsing it into a good post...

			if body_html:
				post_text = strip_html(body_html) #Prefer html because then we don't get linebreak issues
				logging.info('Parsing post from html')
			else:
				post_text = body_text
				logging.info('Parsing post from plain text')

			if not post_text:
				raise Exception('No plain text body in email, html body can\'t be parsed yet!')

			try:
				email_index = post_text.index('post+%s@' % id)
				post_text = post_text[:email_index]
				newline_index = post_text.rstrip().rindex('\n')
				post_text = post_text[:newline_index].strip()
			except:
				logging.info('Failed to remove all crap from post')


			#Strip 'Sent from my iPhone' if it's there. There are probably endless other Sent from
			#we could handle, but hey, I have an iPhone so that's the one I care about...

			post_text = re.sub('\s*Sent from my iPhone\s*$', '', post_text)  
			post_text = post_text.rstrip()
			
			if post.text:
				post.text = post.text + '\r\n\r\n' + Post.seperator + '\r\n\r\n' + post_text
			else:
				post.text = post_text


			self.process_attachments(mail_message, post)

			post.put()

			if is_new_post:
				counter = PostCounter.get()
				counter.increment(post.date.year, post.date.month)
		except:
			log_error('Failed to parse incoming email', traceback.format_exc(6))

	def get_id(self, mail_message):
		to_str = ''.join(mail_message.to)
		match = re.search('post\+([0-9abcdef]{12})@', to_str)

		if not match:
			log_error('Unexpected mail received', 'Got mail with recipient %s', to_str)
			return None
		
		return match.group(1)

	def process_attachments(self, mail_message, post):
		attachments = []

		try:
			attachments = mail_message.attachments
		except exceptions.AttributeError:
			pass #No attachments, then the attribute doesn't even exist :/

		if attachments:
			logging.info('Received %s attachment(s)' % len(attachments))
		
		for attachment in attachments:
			
 			original_filename = attachment.filename
 			encoded_payload = attachment.payload
 			content_id = attachment.content_id
 			if content_id:
 				content_id = content_id.replace('<', '').replace('>', '') # Don't want these around the id, messes with our tag handling
			logging.info('Processing attachment: %s' % original_filename)

			if re.search('\\.(jpe?g|png|bmp|gif)$', original_filename.lower()):
				if post.images is None:
					post.images = []

				bytes = encoded_payload.payload
				if encoded_payload.encoding:
					bytes = bytes.decode(encoded_payload.encoding)
				
				post.has_images = True
				user_image = UserImage()
				img_name = UserImage.create_image_name(original_filename, post.date, post.images)
				user_image.import_image(img_name, original_filename, bytes, post.date, content_id)
				post.images.append(img_name)
				
				user_image.is_inline = False
				if content_id:
					placeholder = '$IMG:' + content_id
					if placeholder in post.text:
						user_image.is_inline = True
						#Ok, lets put in a filename instead of the content_id
						post.text = post.text.replace(placeholder, '$IMG:' + img_name)
				
				user_image.put()

			else:
				logging.warning('Received unsupported attachment, %s' % original_filename)


	def get_bodies(self, mail_message):
		text = ''
		html = ''

		plaintext_bodies = mail_message.bodies('text/plain')
		html_bodies = mail_message.bodies('text/html')

		for content_type, body in html_bodies:
			html += body.decode() + '\n'					

		for content_type, body in plaintext_bodies:
			text += body.decode() + '\n'		

		return text, html			

