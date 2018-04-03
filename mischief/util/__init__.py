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
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from playhouse.postgres_ext import PostgresqlExtDatabase
from werkzeug.routing import IntegerConverter
from os import environ

from .mailgunner import MailGunner

jwt = JWTManager()

cors = CORS()

if environ.get('MISCHIEF_PROD'):
    db = PostgresqlExtDatabase('mischief_db', dsn=environ.get('DATABASE_URL'), register_hstore=False)
else:
    db = PostgresqlExtDatabase('mischief_db', host='localhost', user='postgres', register_hstore=False)

mail = MailGunner()

fredis = FlaskRedis(decode_responses=True)

socketio = SocketIO()


def initialize(app):
    # handle all setup
    from mischief.util.error_handlers import init_error_handlers

    app.url_map.strict_slashes = False
    app.url_map.converters['default'] = IntegerConverter
    jwt.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
    fredis.init_app(app)
    socketio.init_app(app)

    @socketio.on('join')
    def on_join(data):
        room = data['group_id']
        join_room(room)
        emit('join', {'data': 'Successfully joined room: ' + str(room)})

    @socketio.on('leave')
    def on_leave(data):
        room = data['group_id']
        leave_room(room)
        emit('leave', {'data': 'Successfully left room: ' + str(room)})

    from mischief.models.user import User
    from mischief.models.group import Group
    from mischief.models.role import Role
    from mischief.models.feedback import Feedback
    from mischief.models.resource import Resource
    from mischief.models.session_archive import SessionArchive
    # models
    db.connect()
    db.create_tables([User, Group, Role, Feedback, Resource, SessionArchive], safe=True)

    from mischief.views.users_view import UsersView
    from mischief.views.groups_view import GroupsView
    from mischief.views.sessions_view import SessionsView
    # V I E W S
    UsersView.register(app)
    GroupsView.register(app)
    SessionsView.register(app)

    init_error_handlers(app)

    @jwt.jwt_data_loader
    def token_defaults(identity):
        user = User.get(User.id == identity)

        print(current_app.config['JWT_EXPIRES'])
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
