import webapp2

from google.appengine.ext import db

from models import *
from templates import *
from auth import *

# Base handler class

class Handler(webapp2.RequestHandler):
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            "Set-Cookie",
            "%s=%s; Path=/" % (name, cookie_val)
        )

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie("user_id", str(user.key().id()))

    def logout(self):
        self.response.headers.add_header("Set-Cookie", "user_id=; Path=/")

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie("user_id")
        self.user = uid and User.by_id(int(uid))

# Handler class for the home page

class MainHandler(Handler):
    def get(self):
        posts = Post.all().order('-created')
        render(self.response, "front.html", posts = posts)

# Handler class for the login/signup page

class AuthHandler(Handler):
    def get(self):
        render(self.response, "auth.html")

    def post(self):
        have_error = False
        # Register user
        if self.request.get('password-verify'):
            self.username = self.request.get("username")
            self.password = self.request.get("password")
            self.verify = self.request.get("password-verify")
            self.email = self.request.get("email")

            params = dict(username = self.username,
                          email = self.email)

            # validate user input

            if have_error:
                render(self.response, "auth.html", **params)
            else:
                self.register()
        # Log in user
        else:
            self.username = self.request.get("login-name")
            self.password = self.request.get("login-password")

            # validate user input

            if have_error:
                render(self.response, "auth.html", login_name = self.username)
            else:
                user = User.login(self.username, self.password)
                if user:
                    self.login(user)
                    self.redirect("/")
                else:
                    msg = "Incorrect user name or password"
                    render(self.response, "auth.html", login_name = self.username, error_login=msg)

    def register(self):
        u = User.by_name(self.username)
        if u:
            msg = "That user already exists"
            render("auth.html", error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect("/")

# Handler for log out page

class LogoutHandler(Handler):
    def get(self):
        self.logout()
        self.redirect("/auth")

# Handler class for the post permalink page

class PostHandler(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        render(self.response, "permalink.html", post = post)

# Handler class for adding a new blog post

class NewPostHandler(Handler):
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

class WelcomeHandler(Handler):
    def get(self):
        username = self.request.get("username")
        if valid_username(username):
            render(self.response, "welcome.html", username = username)
        else:
            self.redirect("/signup")
