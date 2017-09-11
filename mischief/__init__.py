# -*- coding: utf-8 -*-
"""
mischief
========

mischief is the primary backend component of the
help room management and ticketing platform
'lemming.online'
"""
import os

import mongoengine
from flask import Flask
from flask_jwt import JWT

from mischief.auth import identity, authenticate, random
from mischief.mail import Mail

# app setup
app = Flask('mischief')
app.secret_key = random()
app.config.from_object('mischief.config.Default')
if os.environ.get('MISCHIEF_CONFIG'):
    app.config.from_envvar('MISCHIEF_CONFIG')

# database setup
db = mongoengine.connect(app.config['DB_NAME'], host=app.config['DB_URI'])

# auth setup
jwt = JWT(app, authentication_handler=authenticate, identity_handler=identity)

# mail setup
mail = Mail(app)

from mischief import models, routes  # noqa
