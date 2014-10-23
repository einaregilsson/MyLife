import jinja2, os.path
from models.post import Post

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def get_template(name):
	return JINJA_ENVIRONMENT.get_template(name)

import re
from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(escape(value)))

    result = result.replace(Post.seperator, '<hr>')
    if eval_ctx.autoescape:
        result = Markup(result)
    return result	

JINJA_ENVIRONMENT.filters['nl2br'] = nl2br    