import binascii

import os
from flask import request, url_for
from flask.ext.mail import Message
import argon2

from mischief import app, mail
from mischief.resources import User, Token


@app.route('/user', methods=['POST'])
# TODO: declare request string args, look into marshmallow
def register_user():
    pass
