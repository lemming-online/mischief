# -*- coding: utf-8 -*-
"""
defines the routes that mischief exposes
"""
from flask_jwt import jwt_required
from marshmallow.fields import Email, String
from webargs.flaskparser import use_kwargs, use_args

from mischief import app, mail
from mischief.auth import safe_generate
from mischief.models import User


@app.route('/register', methods=['POST'])
@use_args({
    'email': Email(required=True),
    'first_name': String(required=True),
    'last_name': String(),
    'password': String(required=True),
})
def register(args):
    user = User(**args)
    user.token = safe_generate(ttl=28800)
    user.save()
    registration_message = \
        """
        <h1>welcome to lemming.online!</h1><br>
        <p>please click <a href={}>here</a> to confirm your registration.</p>
        """
    mail.send(registration_message, user.email)
    return user.to_json()


@app.route('/user/<user_id>/confirm', methods=['POST'])
@use_kwargs({
    'token': String(required=True),
})
def confirm_user(user_id, token):
    user = User.objects(id=user_id).first()
    if user.token == token:
        user.token = None
        user.enabled = True
        return user.to_json()
    else:
        return {'message': 'error'}


@app.route('/user/<user_id>')
@jwt_required
def show_user(user_id):
    return User.objects(id=user_id).first().to_json()
