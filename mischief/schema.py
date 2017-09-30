# -*- coding: utf-8 -*-
"""
schema for serializing and deserializing model objects
"""
from marshmallow import Schema
from marshmallow.fields import String, Email, List, Nested


class UserSchema(Schema):
    display_name = String()
    email = Email()
    roles = List(Nested(RoleSchema()))


class RoleSchema(Schema):
    title = String()
    course = Nested(CourseSchema())
    section = Nested(SectionSchema())


class CourseSchema(Schema):
    name = String()
    instructors = List(Nested(UserSchema))


class SectionSchema(Schema):
    name = String()
    location = String()
