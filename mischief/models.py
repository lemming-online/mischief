# -*- coding: utf-8 -*-
"""
defines the data models for mischief.

extends the mongoengine ORM for mongodb.
"""
from mongoengine import Document, EmailField, StringField, BooleanField


class Role:
    """defines the various user roles."""
    ADMIN = 'admin'
    MENTOR = 'mentor'
    MENTEE = 'mentee'

    @staticmethod
    def all():
        """return a tuple with all roles"""
        return Role.ADMIN, Role.MENTOR, Role.MENTEE


class User(Document):
    """
    model for lemming users
    """
    email = EmailField(required=True, unique=True)
    first_name = StringField(required=True, min_length=1, max_length=64)
    last_name = StringField(max_length=64)
    password = StringField()
    role = StringField(required=True, choices=Role.all(), default=Role.MENTEE)
    token = StringField()
    enabled = BooleanField(required=True, default=False)

    def is_enabled(self):
        return self.enabled

    def confirm(self, token):
        """
        confirms the user registration process
        :param token: token from an email
        :return: whether or not confirmation was successful
        """
        if self.token and token == self.token:
            self.token = None
            self.enabled = True
            return True
        return False
