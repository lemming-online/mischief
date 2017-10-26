# -*- coding: utf-8 -*-
"""
random utility setup
"""
import json
from base64 import b64encode
from datetime import datetime
from os import urandom

from bson import ObjectId
from flask import Response, jsonify
from flask_cors import CORS
from flask_jwt_simple import JWTManager
from flask_pymongo import PyMongo, BSONObjectIdConverter
from flask_redis import FlaskRedis

from .mailgunner import MailGunner

jwt = JWTManager()

cors = CORS()

mongo = PyMongo()

mg = MailGunner()

fredis = FlaskRedis(decode_responses=True)

def token_defaults(app, **kwargs):
    return {
        'iss': 'lemming:auth',
        'exp': datetime.utcnow() + app.config['JWT_EXPIRES'],
        'iat': datetime.utcnow(),
        'nbf': datetime.utcnow(),
        'jti': str(b64encode(urandom(48))),  # nonce
        **kwargs,
    }

def initialize(app):
    """
    handle app extension registration and extra setup
    :param app: app to set up with
    """
    from mischief.views import UsersView, ActivationView, AuthenticationView, SectionsView, SessionsView
    from .error_handlers import init_error_handlers

    app.url_map.strict_slashes = False
    app.url_map.converters['default'] = BSONObjectIdConverter
    jwt.init_app(app)
    cors.init_app(app)
    mg.init_app(app)
    mongo.init_app(app)
    fredis.init_app(app)

    @app.before_first_request
    def ensure_indexes():
        mongo.db.users.create_index('email', unique=True)

    # V I E W S
    UsersView.register(app)
    ActivationView.register(app)
    AuthenticationView.register(app)
    SectionsView.register(app)
    SessionsView.register(app)

    init_error_handlers(app)

    class JSONResponse(Response):
        """
        shamelessly stolen from
        https://blog.miguelgrinberg.com/post/customizing-the-flask-response-class
        """
        @classmethod
        def force_type(cls, rv, environ=None):  # pylint: disable=W0221
            if isinstance(rv, (dict, list)):
                rv = jsonify(rv)
            return super().force_type(rv, environ)

    class JSONEncoder(json.JSONEncoder):
        """
        shamelessly stolen from
        https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable
        """
        def default(self, o):  # pylint: disable=E0202
            if isinstance(o, ObjectId):
                return str(o)
            if isinstance(o, bytes):
                return str(o)
            return json.JSONEncoder.default(self, o)

    app.response_class = JSONResponse
    app.json_encoder = JSONEncoder
