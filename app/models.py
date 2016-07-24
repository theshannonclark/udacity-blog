import re
import logging

from google.appengine.ext import db

from templates import *
from auth import *


def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

def users_key(group = "default"):
    return db.Key.from_path("users", group)

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

    def profile_url(self):
        return "/user/%s" % self.name

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    creator = db.ReferenceProperty(User, required = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self, template_path = "post.html", user_name = None):
        self._render_text = self.content.replace('\n', "<br/>")
        return render_str(template_path, p = self, user_name = user_name)

    def render_excerpt(self, limit = -1, user_name = None):
        if limit > -1:
            self._excerpt = self.content
            break_index = self._excerpt.find("\n")
            if break_index > -1:
                self._excerpt = self._excerpt[:break_index]
            self._excerpt = (self._excerpt[:limit]) if len(self._excerpt) > limit else self._excerpt
            self._excerpt = self._excerpt.strip()
            self._excerpt += "..." if not re.compile(".+\.$").match(self._excerpt) else ".."
        return self.render("postexcerpt.html",  user_name = user_name)

    def permalink(self):
        return "/%s" % self.key().id()
