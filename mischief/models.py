# -*- coding: utf-8 -*-
"""
repository for db models
"""
from flask_mongoengine import Document
from mongoengine import EmailField, StringField, BooleanField, ListField, ReferenceField


class User(Document):
    """
    app user model
    """
    email = EmailField(unique=True)
    password = StringField(required=True)
    display_name = StringField(max_length=64)
    admin = BooleanField(default=False)
    roles = ListField(ReferenceField(Role))

    def clean(self):
        # TODO: ensure no conflicting roles
        super().clean()


class Role(Document):
    """
    model associating
    """
    MENTOR = 'mentor'
    MENTEE = 'mentee'

    roles = [MENTOR, MENTEE]

    title = StringField(choices=roles, default=MENTEE)
    course = ReferenceField(Course)
    section = ReferenceField(Section)


class Course(Document):
    """
    course/event model
    """
    name = StringField(required=True)
    instructors = ListField(ReferenceField(User))


class Section(Document):
    """
    meeting template model
    """
    name = StringField(required=True)
    location = StringField()
