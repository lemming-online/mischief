# -*- coding: utf-8 -*-
"""
resource models for mischief's api
"""
from bcrypt import hashpw, checkpw, gensalt
from flask import request
from flask_jwt_simple import create_jwt, jwt_required
from flask_restplus import abort, Resource


from mischief import models, api
from mischief.schema import use_schema, SessionSchema, UsersSchema, UserSchema


@api.route('/sessions')
class Session(Resource):

    @api.doc(security=[])
    @use_schema(SessionSchema)
    def post(self):
        params = request.get_json()
        if params['email'] is None or params['password'] is None:
            abort(400)
        user = models.User.objects.get(email=params['email'])
        if user is None:
            abort(404)
        if checkpw(params['password'].encode('utf-8'), user.password.encode('utf-8')):
            return {'token': create_jwt(identity=user.email)}
        else:
            abort(401)


@api.route('/users')
class Users(Resource):

    @api.doc(security=[])
    @use_schema(UserSchema)
    def post(self):
        params = request.get_json()
        hashed = hashpw(params['password'].encode('utf-8'), gensalt())
        params['password'] = hashed
        user = models.User(**params)
        if user.save(force_insert=True):
            return user
        else:
            abort(404)

    @jwt_required
    @use_schema(UsersSchema)
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

    @use_schema(UserSchema, response_only=True)
    def get(self, user):
        user = models.User.objects.get(id=user)
        if user is not None:
            return user
        else:
            abort(404)
