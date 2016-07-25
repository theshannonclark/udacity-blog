import re
import logging

import webapp2

from google.appengine.ext import db

from models import *
from templates import *
from auth import *


# Base handler class

class Handler(webapp2.RequestHandler):
    def set_secure_cookie(self, name, val, exp = None):
        cookie_val = make_secure_val(val)
        cookie_str = "%s=%s; Path=/" % (name, cookie_val)

        if exp:
            cookie_str = "%s=%s; expires=%s; Path=/" % (name, cookie_val, exp)

        self.response.headers.add_header("Set-Cookie", cookie_str)

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie("user_id", str(user.key().id()))

    def logout(self):
        exp_date = "Thu, 01 Jan 1970 00:00:00 UTC"
        if self.user:
            self.set_secure_cookie("user_id", str(self.user.key().id()), exp_date)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie("user_id")
        self.user = uid and User.by_id(int(uid))

# Handler class for the home page

class MainHandler(Handler):
    def get(self):
        posts = Post.all().order('-created').run(limit = 5)
        render(self.response, "front.html", posts = posts, limit = 500, user = self.user)

# Profile page that shows all posts published by specified user

class UserPostsHandler(Handler):
    def get(self, user_name):
        creator = User.by_name(user_name)

        render(self.response, "userposts.html", limit = 500, user = self.user, creator = creator, user_name = user_name)

# Page to display posts in the specified category

class CategoryHandler(Handler):
    def get(self, category):
        posts = Post.all().filter("category =", category)

        render(self.response, "categoryposts.html", posts = posts, limit = 500, user = self.user, category = category)

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
                params["login_form"] = True
                render(self.response, "auth.html", **params)
            else:
                user = User.login(self.username, self.password)
                if user:
                    self.login(user)
                    self.redirect("/")
                else:
                    params["login_form"] = True
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
            self.redirect("/")
            return

        render(self.response, "permalink.html", post = post, user = self.user)

# Handler class for editing a blog post

class EditPostHandler(Handler):
    def get(self, post_id):
        if not self.user:
            self.redirect("/%s" % post_id)
            return

        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
        if not post:
            self.redirect("/")
            return

        if post.creator.name != self.user.name:
            self.redirect("/%s" % post_id)
            return

        params = dict(
            post_subject = post.subject,
            post_category = post.category,
            post_content = post.content,
            user = self.user
        )
        render(self.response, "newpost.html", **params)

    def post(self, post_id):
        if not self.user:
            self.redirect("/%s" % post_id)
            return

        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
        if not post:
            self.redirect("/")
            return

        if post.creator.name != self.user.name:
            self.redirect("/%s" % post_id)
            return

        have_error = False

        title = self.request.get("subject")
        content = self.request.get("content")
        category = self.request.get('category')

        params = dict(title = post.subject, body = post.content, user = self.user)

        if not (title and content):
            have_error = True
            params["edit_error"] = "Subject and content required"

        if not (self.valid_text(title) and self.valid_text(content)):
            have_error = True
            params["edit_error"] = "Text only, please"

        if have_error:
            render(self.response, "newpost.html", **params)
        else:
            post.subject = title
            post.content = content
            if category:
                post.category = category

            post.put()

            self.redirect("/%s" % post_id)

    def valid_text(self, text):
        return re.compile("^.+$", re.DOTALL).match(text)

# Handler class for deleting a blog post

class DeletePostHandler(Handler):
    def get(self, post_id):
        if not self.user:
            self.redirect("/%s" % post_id)
            return

        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)
        if not post:
            self.redirect("/")
            return

        if post.creator.name != self.user.name:
            self.redirect("/%s" % post_id)
        else:
            db.delete(post)
            self.redirect("/")

# Handler class for adding a new blog post

class NewPostHandler(Handler):
    def get(self):
        render(self.response, "newpost.html", user = self.user)

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        category = self.request.get('category')

        if subject and content:
            p = Post(
                parent = blog_key(),
                subject = subject,
                content = content,
                creator = self.user
            )
            if category:
                p.category = category
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
