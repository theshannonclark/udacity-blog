import webapp2

from google.appengine.ext import db
from models import *
from templates import *


# Handler class for the home page

class MainHandler(webapp2.RequestHandler):
    def get(self):
        posts = Post.all().order('-created')
        render(self.response, "front.html", posts = posts)

# Handler class for the login/signup page

class AuthHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('<form method="post"><input type="submit"/></form>')

    def post(self):
        self.response.write('Authentication request received')

# Handler class for the post permalink page

class PostHandler(webapp2.RequestHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        render(self.response, "permalink.html", post = post)

# Handler class for adding a new blog post

class NewPostHandler(webapp2.RequestHandler):
    def get(self):
        render(self.response, "newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect("/%s" % str(p.key().id()))
        else:
            error = "Subject and content, please!"
            render(self.response, "newpost.html", subject = subject, content = content, error = error)

# Handler class for the welcome page

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        username = self.request.get("username")
        if valid_username(username):
            render(self.response, "welcome.html", username = username)
        else:
            self.redirect("/signup")
