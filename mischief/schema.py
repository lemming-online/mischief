# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from bcrypt import hashpw, gensalt
from bson import ObjectId
from marshmallow import Schema, ValidationError, missing, post_load
from marshmallow.fields import Email, String, Nested, Field, Boolean, URL, Raw

from mischief.mongo import embed_users


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


class MentorSchema(Schema):
    mentor_id = ObjectIdField()
    mentor_ids = ObjectIdField(many=True)


class MenteeSchema(Schema):
    mentee_id = ObjectIdField()
    mentee_ids = ObjectIdField(many=True)


class MischiefSchema(Schema):
    _id = ObjectIdField()


class UserSchema(MischiefSchema):
    email = Email(required=True)
    first_name = String(required=True)
    last_name = String(required=True)
    password = String(load_only=True, required=True)
    is_enabled = Boolean(dump_only=True, default=False)
    mentoring = Nested('SectionSchema',
                       only=('name', 'location', 'description', 'website'), many=True)
    menteeing = Nested('SectionSchema',
                       only=('name', 'location', 'description', 'website'), many=True)
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
    website = URL()
    mentors = Nested(UserSchema, only=('email', 'first_name', 'last_name', '_id'), many=True)
    mentees = Nested(UserSchema, only=('email', 'first_name', 'last_name', '_id'), many=True)
    mentor_id = ObjectIdField(load_only=True, required=True)

    def get_mentor(self, data):
        if 'mentor_id' in data:
            data['mentors'] = embed_users([data['mentor_id']], error=True)
        return data

    @post_load
    def preprocess(self, data):
        data = self.get_mentor(data)
        return data
