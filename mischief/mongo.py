# -*- coding: utf-8 -*-
"""
mongo helpers
"""
from flask import abort
from mischief.util import mongo as m

# side effect helpers (READS/WRITES TO DB)

def make_instructor(data, for_id):
    return m.db.users.update_one(data,
                                 {'$push': {'courses': embed_course(for_id)}})

def add_section(data, to_id):
    return m.db.courses.update_one({'_id': to_id},
                                   {'$push', {'sections': data}})

def user_fields(u):
    return {
        'email': u['email'],
        'first_name': u['first_name'],
        'last_name': u['last_name'],
        '_id': u['_id']
    }

def update_user(user_id):
    user = user_by_id(user_id)
    m.db.courses.update_many({'instructor._id': user_id},
                             {'$set': {'instructor': user_fields(user)}})
    m.db.users.update_many({'courses.instructor._id': user_id},
                           {'$set': {'courses.*.instructor': user_fields(user)}})
    return user_by_id(user_id)

def delete_user(user_id):
    user = user_by_id(user_id)
    if user.get('instructing'):
        abort(400)
    else:
        return m.db.users.delete_one({'_id': user_id})

def update_course(course_id):
    course = course_by_id(course_id)
    m.db.users.update_one({'_id': course['instructor']['_id']},
                          {'$set': {'courses.$': course}})
    return course_by_id(course_id)

def delete_course(course_id):
    course = course_by_id(course_id)
    m.db.users.update_one({'_id': course['instructor']['_id']},
                          {'$pull': {'courses': {'_id': course_id}}})
    return m.db.courses.delete_one({'_id': course_id})

# get document helpers (READS FROM DB)

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
    if error:
        return m.db.courses.find_one_or_404({'sections._id': id}, {'sections.$': True})

# serialize document helpers (READS FROM DB)

def embed_users(ids):
    return [embed_user(id) for id in ids]

def embed_user(id):
    user = user_by_id(id)
    return {
        'first_name': user['first_name'],
        'email': user['email'],
        '_id': user['_id']
    }

def embed_sections(ids):
    return [embed_section(id) for id in ids]

def embed_section(id, role='mentee'):
    section = section_by_id(id)
    return {
        'role': role,
        'name': section['name'],
        'location': section['location'],
        '_id': section['_id']
    }

def embed_courses(ids):
    return [embed_course(id) for id in ids]

def embed_course(id, instructor=False):
    course = course_by_id(id)
    return {
        'name': course['name'],
        'instructor': instructor,
        'website': course['website'],
        'description': course['descripion'],
        '_id': course['_id']
    }
