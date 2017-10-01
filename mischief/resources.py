# -*- coding: utf-8 -*-
"""
REST resource views
"""
from flask.views import MethodView

from mischief import app, mongo
from mischief.schema import RegisteredUserSchema


# noinspection PyMethodMayBeStatic
@app.resource(endpoint='user_api', url='/users', pk='user_id')
class UserResource(MethodView):
    def get(self, user_id):
        pass

    def put(self, user_id):
        pass

    def patch(self, user_id):
        pass

    def delete(self, user_id):
        pass


@app.resource(endpoint='users_api', url='/users')
class UsersResource(MethodView):
    @app.use_schema(RegisteredUserSchema(), load=True)
    def post(self, data):
        if data.acknowledged:
            return mongo.db.users.find_one_or_404({'_id': data.inserted_id})
        else:
            return {'error': {'status_code': 500}}

    @app.use_schema(RegisteredUserSchema(), many=True)
    def get(self):
        return mongo.db.users.find()
