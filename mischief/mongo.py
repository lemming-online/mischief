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

def embed_users(ids, error=False):
    return [embed_user(id, error) for id in ids]

def embed_user(id, error=False):
    user = user_by_id(id, error)
    return {
        '_id': user.get('_id'),
        'first_name': user.get('first_name'),
        'last_name': user.get('last_name'),
        'email': user.get('email'),
    }

def embed_sections(ids):
    return [embed_section(id) for id in ids]

def embed_section(id):
    section = section_by_id(id)
    return {
        '_id': section.get('_id'),
        'name': section.get('name'),
        'location': section.get('location'),
        'description': section.get('description'),
        'website': section.get('website')
    }
