import os

import jinja2
import webapp2

from models import *

template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

# Base handler class from Udacity Intro to Backend course
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        template = jinja_env.get_template(template)
        return template.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainHandler(Handler):
    def get(self):
        self.response.write('Hello, world!')

class AuthHandler(Handler):
    def get(self):
        self.response.write('<form method="post"><input type="submit"/></form>')

    def post(self):
        self.response.write('Authentication request received')