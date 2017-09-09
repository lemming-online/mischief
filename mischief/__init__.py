# -*- coding: utf-8 -*-
"""
mischief
========

mischief is the primary backend component of the
help room management and ticketing platform
'lemming.online'
"""
import mongoengine
from flask import Flask
from flask_jwt import JWT

from mischief.auth import identity, authenticate
from mischief.mail import Mail


# app setup
app = Flask('mischief')
app.config.from_object('mischief.default_config.DefaultConfig')
try:
    app.config.from_object('mischief.config.Config')
except ImportError:
    pass
try:
    app.config.from_envvar('MISCHIEF_CONFIG')
except RuntimeError:
    pass

# database setup
db = mongoengine.connect(app.config['DB_NAME'], host=app.config['DB_URI'])


# auth setup
jwt = JWT(app, authentication_handler=authenticate, identity_handler=identity)

# mail setup
mail = Mail(app)

from mischief import models, routes  # noqa
