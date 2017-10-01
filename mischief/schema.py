# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from flask import request
from marshmallow import Schema, post_load
from marshmallow.fields import String, Email, Nested, Boolean
from marshmallow.validate import OneOf

from mischief import mongo
from mischief.enum import RoleNames


class SectionSchema(Schema):
    name = String(required=True)
    location = String()


class CourseSchema(Schema):
    name = String(required=True)
    sections = Nested(SectionSchema, many=True, default=[])


class RoleSchema(Schema):
    title = String(
        default=RoleNames.mentee,
        validate=OneOf([r.value for r in RoleNames])
    )
    course = Nested(CourseSchema, only=('name',), required=True)
    section = Nested(SectionSchema, required=True)


class UserSchema(Schema):
    display_name = String(required=True)
    roles = Nested(RoleSchema, many=True, default=[])
    enabled = Boolean(default=False, load_only=True)
    admin = Boolean(default=False, load_only=True)

    # TODO: DRY-ify this by making the collection parameterized
    @post_load
    def make_user(self, data):
        if request.method == 'POST':
            return mongo.db.users.insert_one({
                **data
            })
        else:
            return mongo.db.users.update_one({**data},
                                             {**data})


class RegisteredUserSchema(UserSchema):
    email = Email(unique=True, required=True)
    password = String(load_only=True, required=True)
