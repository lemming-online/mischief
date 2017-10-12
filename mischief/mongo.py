# -*- coding: utf-8 -*-
"""
mongo helpers
"""
from mischief.util import mongo as m

# get document helpers (READS FROM DB)

def by_id(document_type, id, error=False):
    if error:
        return m.db[document_type].find_one_or_404({'_id': id})
    else:
        return m.db[document_type].find_one({'_id': id})

def user_by_id(id, error=False):
    return by_id('users', id, error)

def section_by_id(id, error=False):
    return by_id('sections', id, error)

# serialize document helpers (READS FROM DB)

def embed_users(ids):
    return [embed_user(id) for id in ids]

def embed_user(id):
    user = user_by_id(id)
    return {
        '_id': user['_id'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'email': user['email'],
    }

def embed_sections(ids):
    return [embed_section(id) for id in ids]

def embed_section(id, role='mentee'):
    section = section_by_id(id)
    return {
        '_id': section['_id'],
        'name': section['name'],
        'location': section['location'],
        'description': section['description'],
        'website': section['website']
    }
