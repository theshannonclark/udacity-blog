import webapp2

from models import *

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello, world!')