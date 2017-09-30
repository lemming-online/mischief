# -*- coding: utf-8 -*-
"""
REST resource views
"""
from flask.views import MethodView

from mischief.helpers import register_api
from mischief.models import User
from mischief.schema import UserSchema


def resource(endpoint, url, pk='id', pk_type='string'):
    class Resource:
        def __init__(self, resource_cls):
            self.endpoint = endpoint
            self.url = url
            self.pk = pk
            self.pk_type = pk_type
            register_api(resource_cls, endpoint, url, pk, pk_type)
    return Resource


@resource(endpoint='user_api', url='/users/', pk='user_id')
class UserResource(MethodView):
    def get(self, user_id):
        if user_id is None:
            return [UserSchema().dump(user) for user in User.objects()]
        else:
            return UserSchema().dump(User.objects(id=user_id))
