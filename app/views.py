import re

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
        render(self.response, "front.html", posts = posts, user = self.user)

# Handler class for the login/signup page

class AuthHandler(Handler):

    email_regex = re.compile("^[\w\d\-\.]+@[\w\d\-\.]+\.[a-z]+$")

    def get(self):
        render(self.response, "auth.html")

    def post(self):
        have_error = False
        # Register user
        if self.request.get('form-type') == "signup":
            self.username = self.request.get("username")
            self.password = self.request.get("password")
            self.verify = self.request.get("password-verify")
            self.email = self.request.get("email")

            params = dict(username = self.username,
                          email = self.email)

            # validate user input

            if not (self.username and self.password and self.verify):
                have_error = True
                params["signup_error"] = "Something is missing..."

            if not self.valid_username(self.username):
                have_error = True
                params["username_error"] = "Username must be letters and numbers"

            if self.password != self.verify:
                have_error = True
                params["password_error"] = "Password and verify password must match"

            if self.email and (not self.valid_email(self.email)):
                have_error = True
                params["email_error"] = "Email must contain an @ character, and end with a dot followed by letters"

            if have_error:
                render(self.response, "auth.html", **params)
            else:
                self.register()
        # Log in user
        else:
            self.username = self.request.get("login-name")
            self.password = self.request.get("login-password")

            params = dict(login_name = self.username)

            # validate user input

            if not self.valid_username(self.username):
                have_error = True
                params["error_login_name"] = "Username must be letters and numbers"

            if have_error:
                render(self.response, "auth.html", **params)
            else:
                user = User.login(self.username, self.password)
                if user:
                    self.login(user)
                    self.redirect("/")
                else:
                    params["error_login"] = "Incorrect user name or password"
                    render(self.response, "auth.html", **params)

    def register(self):
        u = User.by_name(self.username)
        if u:
            msg = "That user already exists"
            render(self.response, "auth.html", username_error = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect("/")

    def valid_username(self, username):
        return username.isalnum()

    def valid_email(self, email):
        return self.email_regex.match(email)

    # Only logged-out users can sign up/log in
    def initialize(self, *a, **kw):
        super(AuthHandler, self).initialize(*a, **kw)
        if self.user:
            self.redirect("/")

# Handler for log out page

class LogoutHandler(Handler):
    def get(self):
        if self.user:
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

        render(self.response, "permalink.html", post = post, user = self.user)

# Handler class for adding a new blog post

class NewPostHandler(Handler):
    def get(self):
        render(self.response, "newpost.html", user = self.user)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(
                parent = blog_key(),
                subject = subject,
                content = content,
                creator = self.user
            )
            p.put()
            self.redirect("/%s" % str(p.key().id()))
        else:
            error = "Subject and content, please!"
            render(self.response, "newpost.html", subject = subject, content = content, error = error, user = self.user)

    # Only logged in users can post
    def initialize(self, *a, **kw):
        super(NewPostHandler, self).initialize(*a, **kw)
        if not self.user:
            self.redirect("/auth")
