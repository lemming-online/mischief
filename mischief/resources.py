# -*- coding: utf-8 -*-
"""
resource models for mischief's api
"""
from bcrypt import hashpw, checkpw, gensalt
from flask import request
from flask_jwt_simple import create_jwt, jwt_required
from flask_restplus import abort, Resource
from flask_restplus.fields import List, Nested, String

from mischief import models, api

session_fields = api.model('Session', {
    'email': String,
    'password': String
})


@api.route('/session')
class Session(Resource):
    @api.marshal_with(session_fields)
    def post(self):
        params = request.get_json()
        if params['email'] is None or params['password'] is None:
            abort(400)
        user = models.User.objects.get(email=params['email'])
        if user is None:
            abort(404)
        if checkpw(params['password'].encode('utf-8'), user.password):
            return {'token': create_jwt(identity=user.email)}
        else:
            abort(401)

user_fields = api.model('User', {
    'id': String,
    'email': String,
    'first_name': String,
    'last_name': String
})

users_fields = api.model('Users', {
    'users': List(Nested(user_fields)),
})


@api.route('/users')
class Users(Resource):
    decorators = [jwt_required]

    @api.marshal_with(user_fields)
    def post(self):
        params = request.get_json()
        hashed = hashpw(params['password'].encode('utf-8'), gensalt())
        params['password'] = hashed
        user = models.User(**params)
        if user.save(force_insert=True):
            return user
        else:
            abort(404)

    @api.marshal_with(users_fields)
    def get(self):
        return {'users': models.User.objects.only(
            'id',
            'email',
            'first_name',
            'last_name'
        ).all()}


@api.route('/users/<user>')
class User(Resource):
    decorators = [jwt_required]

    @api.marshal_with(user_fields)
    def get(self, user):
        user = models.User.objects.get(id=user)
        if user is not None:
            return user
        else:
            abort(404)
