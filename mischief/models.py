# -*- coding: utf-8 -*-
"""
repository for db models
"""
from flask_mongoengine import Document
from mongoengine import EmailField, StringField, BooleanField


class User(Document):
    """
    app user model
    """
    email = EmailField(unique=True)
    password = StringField(required=True)
    first_name = StringField(max_length=64)
    last_name = StringField(max_length=64)
    admin = BooleanField(default=False)
