# -*- coding: utf-8 -*-
"""
defines the routes that mischief exposes
"""
from flask import url_for, request
from flask_jwt import jwt_required
from marshmallow.fields import Email, String
from webargs.flaskparser import use_args

from mischief import app, mail
from mischief.auth import random
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
    user.token = random(ttl=28800)
    user.save()
    registration_message = \
        """
        <h1>welcome to lemming.online!</h1><br>
        <form action='{}' method='post'>
        <p>please click below to confirm your account registration.</p>
        <input type='hidden' value='{}'>
        <input type='submit' value='confirm'>
        </form>
        """.format(url_for('confirm_user', user_id=user.id, _external=True), user.token)
    mail.send(registration_message, user.email)
    return user.to_json()


@app.route('/user/<user_id>/confirm', methods=['POST'])
def confirm_user(user_id):
    user = User.objects(id=user_id).first()
    if user.confirm(request.form['token']):
        return user.to_json()
    else:
        user.delete()
        return {'error': 'could not confirm, please try to reregister'}, 401


@app.route('/user/<user_id>')
@jwt_required
def show_user(user_id):
    return User.objects(id=user_id).first().to_json()
