# -*- coding: utf-8 -*-
"""
mischief
========

mischief is the primary backend component of the
help room management and ticketing platform
'lemming.online'
"""
import os

from flask import logging
from flask_cors import CORS
from flask_jwt_simple import JWTManager
from flask_pymongo import PyMongo

from .ratnap import RatNap

# app setup
app = RatNap('mischief')
app.config.from_object('mischief.config.Default')
if os.environ.get('MISCHIEF_CONFIG'):
    app.config.from_envvar('MISCHIEF_CONFIG')

# db setup
mongo = PyMongo(app)

# jwt setup
jwt = JWTManager(app)

# CORS setup
CORS(app)

logging.getLogger('flask_cors').level = logging.DEBUG


# set mongo indexes
@app.before_first_request
def ensure_indexes():
    mongo.db.users.create_index('email', unique=True)


# set admin user
@app.before_first_request
def ensure_admin():
    mongo.db.users.find_one_and_replace({'email': 'team@lemming.online'},
                                        {
                                            'email': 'team@lemming.online',
                                            'password': 'lemming',
                                            'display_name': 'Team Lemming',
                                            'roles': [],
                                            'admin': True
                                        },
                                        upsert=True)


# format all responses
@app.after_request
def conform_to_jsend(response):
    if response.status_code in range(200, 299):
        data = {
            'status': 'success',
            'data': response.data
        }
        response.data = data
    if response.status_code in range(400, 499):
        data = {
            'status': 'fail',
            'data': response.data
        }
        response.data = data
    if response.status_code in range(500, 599):
        data = {
            'status': 'error',
            'message': response.status,
            'code': response.status_code,
            'data': response.data
        }
        response.data = data
    return response

from mischief import resources, routes  # noqa
