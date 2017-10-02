# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from bson import ObjectId
from flask import request
from marshmallow import Schema, post_load, ValidationError
from marshmallow.fields import String, Email, Nested, Boolean, DateTime
from marshmallow.validate import OneOf

from mischief import mongo
from mischief.enum import RoleNames


class MischiefSchema(Schema):
    _mongo_document_name = NotImplementedError

    _id = String(dump_only=True)

    @post_load
    def make_mongo(self, data):
        if data is None:
            raise ValidationError('No data provided')
        if data.get('_id'):
            data['_id'] = ObjectId(data['_id'])
        if request.method == 'POST':
            return mongo.db[self._mongo_document_name].insert_one({**data})
        else:
            return mongo.db[self._mongo_document_name].update_one({**data},
                                                               {**data})


class SectionSchema(MischiefSchema):
    _mongo_document_name = 'sections'

    name = String(required=True)
    location = String()


class CourseSchema(MischiefSchema):
    _mongo_document_name = 'courses'

    name = String(required=True)
    sections = Nested(SectionSchema, many=True, default=[])


class RoleSchema(MischiefSchema):
    _mongo_document_name = 'roles'

    title = String(
        default=RoleNames.mentee,
        validate=OneOf([r.value for r in RoleNames])
    )
    course = Nested(CourseSchema, only=('name',), required=True)
    section = Nested(SectionSchema, required=True)


class UserSchema(MischiefSchema):
    display_name = String(required=True)
    roles = Nested(RoleSchema, many=True, default=[])
    enabled = Boolean(default=False, load_only=True)
    admin = Boolean(default=False, load_only=True)


class RegisteredUserSchema(UserSchema):
    _mongo_document_name = 'users'

    email = Email(unique=True, required=True)
    password = String(load_only=True, required=True)
