# -*- coding: utf-8 -*-
"""
mischief
========

mischief is the primary backend component of the
help room management and ticketing platform
'lemming.online'
"""
import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_simple import JWTManager
from flask_mongoengine import MongoEngine
from flask_restplus import Api

# app setup
app = Flask('mischief')
app.config.from_object('mischief.config.Default')
if os.environ.get('MISCHIEF_CONFIG'):
    app.config.from_envvar('MISCHIEF_CONFIG')

# db setup
db = MongoEngine(app)

# api setup
authorizations = {
    'bearerAuth': {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'JWT'
    }
}
api = Api(app, authorizations=authorizations, security='token')

# jwt setup
jwt = JWTManager(app)

# CORS setup
CORS(app)

from mischief import routes, resources  # noqa
