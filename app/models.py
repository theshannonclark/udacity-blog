import logging

from google.appengine.ext import db

from templates import *
from auth import *


def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

def users_key(group = "default"):
    return db.Key.from_path("users", group)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', "<br/>")
        return render_str("post.html", p = self)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter("name = ", name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(
            parent = users_key(),
            name = name,
            pw_hash = pw_hash,
            email = email
        )

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_password(name, pw, u.pw_hash):
            return u
