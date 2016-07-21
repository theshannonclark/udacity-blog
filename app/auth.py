import os
import random
import hashlib
import binascii
import hmac


secret = "'KT?|S$)[XtoD|&efbpWBV4-mw59x}QwWVt9Pa7u01c&~<&A`)~)2M]-FJ8A5-ja*');"

def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split("|")[0]
    if hmac.compare_digest(secure_val, make_secure_val(val)):
        return val

def make_salt(length = 16):
    return binascii.hexlify(os.urandom(16))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s,%s" % (salt, h)

def valid_password(name, password, h):
    salt = h.split(",")[0]
    return make_pw_hash(name, password, salt) == h