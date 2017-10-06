# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from bcrypt import hashpw, gensalt
from bson import ObjectId
from marshmallow import Schema, ValidationError, missing, post_load
from marshmallow.fields import Email, String, Nested, Field, DateTime, Boolean, URL, Raw


class EmailSchema(Schema):
    email = Email(required=True, load_only=True)


class AuthenticationSchema(Schema):
    email = Email(required=True, load_only=True)
    password = String(required=True, load_only=True)


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
    last_name = String()
    photo = URL(dump_only=True)
    password = String(load_only=True)
    is_enabled = Boolean(default=False)
    instructing = Nested('CourseSchema', only=('name', 'id'), many=True, default=[])
    mentoring = Nested('SectionSchema', only=('name', 'location', 'id'), many=True, default=[])
    menteeing = Nested('SectionSchema', only=('name', 'location', 'id'), many=True, default=[])

    @post_load
    def hash_password(self, data):
        if data.get('password'):
            data['password'] = hashpw(data['password'].encode('utf8'), gensalt())


class UserImageSchema(Schema):
    photo = Raw(required=True, load_only=True)


class SectionSchema(MischiefSchema):
    name = String(required=True)
    location = String()
    mentors = Nested(UserSchema, only=('display_name', 'email', 'id'), many=True)
    mentees = Nested(UserSchema, only=('display_name', 'email', 'id'), many=True)
    course = Nested('CourseSchema', only=('name', 'instructor', 'id'))
    archive = Nested('ArchiveSchema', only=('at', 'id'))
    wiki = NotImplementedError  # TODO


class ArchiveSchema(MischiefSchema):
    finished_at = DateTime(required=True)
    tickets = Nested('TicketSchema', many=True)


class TicketSchema(MischiefSchema):
    title = String(required=True)
    content = String(required=True)
    poster = Nested(UserSchema, only=('display_name', 'email', 'id'))
    handled = Boolean(required=True, default=False)
    handled_by = Nested(UserSchema, only=('display_name', 'email', 'id'))


class CourseSchema(MischiefSchema):
    name = String()
    instructor = Nested(UserSchema, only=('first_name', 'last_name', 'email', 'id'))
    sections = Nested(SectionSchema, many=True)
