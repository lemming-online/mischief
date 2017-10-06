# -*- coding: utf-8 -*-
"""
mongo helpers
"""
from mischief.util import mongo as m

def by_id(document_type, id, error=False):
    if error:
        return m.db[document_type].find_one_or_404({'_id': id})
    else:
        return m.db[document_type].find_one({'_id': id})

def user_by_id(id, error=False):
    return by_id('users', id, error)

def course_by_id(id, error=False):
    return by_id('courses', id, error)

def section_by_id(id, error=False):
    return by_id('sections', id, error)

def embed_users(ids):
    return [embed_user(id) for id in ids]

def embed_user(id):
    user = user_by_id(id)
    return {
        'first_name': user['first_name'],
        'email': user['email'],
        'id': user['_id']
    }

def embed_sections(ids):
    return [embed_section(id) for id in ids]

def embed_section(id):
    section = section_by_id(id)
    return {
        'name': section['name'],
        'location': section['location'],
        'id': section['_id']
    }

def embed_courses(ids):
    return [embed_course(id) for id in ids]

def embed_course(id):
    course = course_by_id(id)
    return {
        'name': course['name'],
        'instructor': course['instructor'],
        'id': course['_id']
    }
