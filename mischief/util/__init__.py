# -*- coding: utf-8 -*-
"""
random utility setup
"""
import json
from base64 import b64encode
from datetime import datetime
from os import urandom

from bson import ObjectId
from flask import Response, jsonify, current_app
from flask_cors import CORS
from flask_jwt_simple import JWTManager
from flask_redis import FlaskRedis
from peewee import PostgresqlDatabase
from werkzeug.routing import IntegerConverter

from .mailgunner import MailGunner

jwt = JWTManager()

cors = CORS()

db = PostgresqlDatabase('mischief_db')

mail = MailGunner()

fredis = FlaskRedis(decode_responses=True)


def initialize(app):
    # handle all setup
    from mischief.util.error_handlers import init_error_handlers

    app.url_map.strict_slashes = False
    app.url_map.converters['default'] = IntegerConverter
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
    fredis.init_app(app)

    from mischief.models.user import User
    from mischief.models.group import Group
    from mischief.models.user_groups import UserGroups
    # models
    db.connect()
    db.create_tables([User, Group, UserGroups], safe=True)

    from mischief.views.users_view import UsersView
    # V I E W S
    UsersView.register(app)

    init_error_handlers(app)

    @jwt.jwt_data_loader
    def token_defaults(identity):
        user = User.get(User.id == identity)
        return {
            'iss': 'lemming:auth',
            'exp': datetime.utcnow() + current_app.config['JWT_EXPIRES'],
            'iat': datetime.utcnow(),
            'nbf': datetime.utcnow(),
            'jti': str(b64encode(urandom(48))),  # nonce
            'sub': user.email,
            'fnm': user.first_name,
            'lnm': user.last_name,
            'uid': user.id,
        }

    class JSONResponse(Response):
        """
        shamelessly stolen from
        https://blog.miguelgrinberg.com/post/customizing-the-flask-response-class
        """
        @classmethod
        def force_type(cls, rv, environ=None):
            if isinstance(rv, (dict, list)):
                rv = jsonify(rv)
            return super().force_type(rv, environ)

    app.response_class = JSONResponse
