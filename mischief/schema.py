# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
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
    sections = Nested(SectionSchema, many=True)


class RoleSchema(Schema):
    title = String(
        default=RoleNames.mentee,
        validate=OneOf([r.value for r in RoleNames])
    )
    course = Nested(CourseSchema, only=('name',))
    section = Nested(SectionSchema)


class UserSchema(Schema):
    display_name = String()
    roles = Nested(RoleSchema, many=True, default=[])
    enabled = Boolean(default=False, load_only=True)
    admin = Boolean(default=False, load_only=True)

    # TODO: DRY-ify this by making the collection parameterized
    @post_load
    def make_user(self, data):
        return mongo.db.users.insert_one({
            **data
        })


class RegisteredUserSchema(UserSchema):
    email = Email(unique=True, required=True)
    password = String(load_only=True)
