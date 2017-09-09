# -*- coding: utf-8 -*-
"""
contains authentication helpers for mischief.

currently using flask-jwt.
"""
import binascii
import os
from time import time as now

from argon2 import argon2_hash
from werkzeug.security import safe_str_cmp

from mischief.models import User


def safe_generate(ttl=None):
    """generate a random token, with an optional embedded TTL"""
    safe = binascii.hexlify(os.urandom(24))
    if ttl:
        safe += bytes(':{}'.format(now() + ttl), 'utf8')


def is_expired(token):
    """naively examine the TTL in a generated token"""
    _, time = token.split(':')
    return now() > time


def authenticate(email, password):
    """attempt to authenticate for the given identity."""
    user = User.objects(email=email).first()
    if user and user.is_enabled() and safe_str_cmp(user.password, argon2_hash(password, user.password)):
        return user


def identity(payload):
    """return the user id given a payload."""
    return User.objects(id=payload['identity']).first()
