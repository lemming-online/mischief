# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from bcrypt import hashpw, gensalt
from bson import ObjectId
from marshmallow import Schema, ValidationError, missing, post_load
from marshmallow.fields import Email, String, Nested, Field, DateTime, Boolean, URL, Raw, List

from mischief.mongo import user_by_id, course_by_id, section_by_id, embed_user, embed_users, embed_section, embed_sections, embed_course, embed_courses


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
    password = String(load_only=True)
    is_enabled = Boolean(default=False)
    instructing_ids = List(ObjectIdField, load_only=True)
    instructing = Nested('CourseSchema', only=('name', 'instructor', 'id'), many=True, default=[])
    mentoring_ids = List(ObjectIdField, load_only=True)
    mentoring = Nested('SectionSchema', only=('name', 'location', 'id'), many=True, default=[])
    menteeing_ids = List(ObjectIdField, load_only=True)
    menteeing = Nested('SectionSchema', only=('name', 'location', 'id'), many=True, default=[])
    image = URL(dump_only=True)

    @post_load
    def make_user(self, data):
        if 'password' in data:
            data['password'] = hashpw(data['password'].encode('utf8'), gensalt())
        if 'instructing_ids' in data:
            data['instructing'] = embed_courses(data['instructing_ids'])
        if 'mentoring_ids' in data:
            data['mentoring'] = embed_sections(data['mentoring_ids'])
        if 'menteeing_ids' in data:
            data['menteeing'] = embed_sections(data['menteeing_ids'])
        return data


class UserImageSchema(Schema):
    image = Raw(required=True, load_only=True)


class SectionSchema(MischiefSchema):
    name = String(required=True)
    location = String()
    mentor_ids = List(ObjectIdField, load_only=True)
    mentors = Nested(UserSchema, only=('first_name', 'email', 'id'), many=True, default=[])
    mentee_ids = List(ObjectIdField, load_only=True)
    mentees = Nested(UserSchema, only=('first_name', 'email', 'id'), many=True, default=[])
    course_id = ObjectIdField(required=True, load_only=True)
    course = Nested('CourseSchema', only=('name', 'instructor', 'id'))
    archive = Nested('ArchiveSchema', only=('at', 'id'))
    wiki = NotImplementedError  # TODO

    @post_load
    def make_section(self, data):
        if 'mentor_ids' in data:
            data['mentors'] = embed_users(data['mentor_ids'])
        if 'mentee_ids' in data:
            data['mentees'] = embed_users(data['mentee_ids'])
        if 'course_id' in data:
            data['course'] = embed_course(data['course_id'])
        return data


class ArchiveSchema(MischiefSchema):
    finished_at = DateTime(required=True)
    tickets = Nested('TicketSchema', many=True)


class TicketSchema(MischiefSchema):
    title = String(required=True)
    content = String(required=True)
    poster = Nested(UserSchema, only=('display_name', 'email', 'id'), required=True)
    handled = Boolean(required=True, default=False)
    handled_by = Nested(UserSchema, only=('display_name', 'email', 'id'))


class CourseSchema(MischiefSchema):
    name = String(required=True)
    instructor_id = ObjectIdField(required=True, load_only=True)
    instructor = Nested(UserSchema, only=('first_name', 'last_name', 'email', 'id'))
    section_ids = List(ObjectIdField, load_only=True)
    sections = Nested(SectionSchema, only=('name', 'location', 'id'), many=True, default=[])

    @post_load
    def make_course(self, data):
        if 'instructor_id' in data:
            data['instructor'] = embed_user(data['instructor_id'])
        if 'section_ids' in data:
            data['sections'] = embed_sections(data['section_ids'])
        return data




