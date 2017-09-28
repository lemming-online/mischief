# -*- coding: utf-8 -*-
"""
resource models for mischief's request and response schema
"""
from flask_restplus.fields import String, List, Nested

from mischief import api


def use_schema(schema_cls, request_only=False, response_only=False):
    def decorated(fn):
        if not (schema_cls.request_schema() is None or response_only):
            fn = api.expect(schema_cls.request_schema())(fn)
        if not (schema_cls.response_schema() is None or request_only):
            fn = api.marshal_with(schema_cls.response_schema())(fn)
        return fn
    return decorated


class BaseSchema:
    @staticmethod
    def request_schema():
        raise NotImplementedError

    @staticmethod
    def response_schema():
        raise NotImplementedError


class SessionSchema(BaseSchema):
    @staticmethod
    def request_schema():
        return api.model('SessionRequest', {
            'email': String,
            'password': String
        })

    @staticmethod
    def response_schema():
        return api.model('SessionResponse', {
            'token': String
        })


class UserSchema(BaseSchema):
    @staticmethod
    def request_schema():
        return api.model('UserRequest', {
            'email': String,
            'password': String,
            'first_name': String,
            'last_name': String
        })

    @staticmethod
    def response_schema():
        return api.model('UserResponse', {
            'id': String,
            'email': String,
            'first_name': String,
            'last_name': String
        })


class UsersSchema(BaseSchema):
    @staticmethod
    def request_schema():
        return None

    @staticmethod
    def response_schema():
        return api.model('Users', {
            'users': List(Nested(UserSchema.response_schema())),
        })
