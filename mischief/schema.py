# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from bcrypt import hashpw, gensalt
from bson import ObjectId
from flask import abort
from marshmallow import Schema, ValidationError, missing, post_load
from marshmallow.fields import Email, String, Nested, Field, DateTime, Boolean, URL, Raw, List

from mischief.mongo import user_by_id, course_by_id, embed_user

# deserializing only
class EmailSchema(Schema):
    email = Email(required=True, load_only=True)

# deserializing only
class AuthenticationSchema(Schema):
    email = Email(required=True, load_only=True)
    password = String(required=True, load_only=True)

# deserializing only
class UserImageSchema(Schema):
    image = Raw(required=True, load_only=True)


class ObjectIdField(Field):
    """field for mongodb ObjectId"""
    def _deserialize(self, value, attr, data):
        try:
            return ObjectId(value)
        except:
            raise ValidationError('invalid ObjectId `%s`' % value)

    def _serialize(self, value, attr, obj):
        if value is None:
            return missing
        return str(value)


class MischiefSchema(Schema):
    _id = ObjectIdField()


class UserSchema(MischiefSchema):
    email = Email(required=True)
    first_name = String(required=True)
    last_name = String(required=True)
    password = String(load_only=True)
    is_enabled = Boolean(default=False)
    courses = Nested('EmbeddedCourseSchema', many=True)
    image = URL()

    def clean_password(self, data):
        if 'password' in data:
            data['password'] = hashpw(data['password'].encode('utf8'), gensalt())
        return data

    @post_load
    def preprocess(self, data):
        data = self.clean_password(data)
        return data


class SectionSchema(MischiefSchema):
    name = String(required=True)
    location = String()
    description = String()
    mentors = Nested(UserSchema, only=('email', 'first_name', 'last_name', '_id'), many=True)
    mentees = Nested(UserSchema, only=('email', 'first_name', 'last_name', '_id'), many=True)


class CourseSchema(MischiefSchema):
    name = String(required=True)
    website = URL(default="")
    description = String(default="")
    instructor = Nested(UserSchema, only=('email', 'first_name', 'last_name', '_id'))
    sections = Nested(SectionSchema, many=True)

    # deserialization only
    instructor_id = ObjectIdField(required=True, load_only=True)

    @post_load
    def preprocess(self, data):
        if 'instructor_id' in data:
            data['instructor'] = embed_user(data.pop('instructor_id'))
            return data
        else:
            raise ValidationError('Instructor ID required.')


class EmbeddedSectionSchema(MischiefSchema):
    role = String(default='mentee')
    name = String(required=True)
    location = String()
    description = String()

class EmbeddedCourseSchema(MischiefSchema):
    instructor = Boolean(required=True, default=False)
    name = String(required=True)
    website = URL(default="")
    description = String(default="")
    sections = Nested(EmbeddedSectionSchema, many=True)
