# -*- coding: utf-8 -*-
"""
REST resource views
"""
import boto3
import jwt
from bcrypt import checkpw
from flask import abort, url_for
from flask_classful import FlaskView, route
from flask_jwt_simple import create_jwt, jwt_required

from mischief.mongo import user_by_id, section_by_id, embed_user, embed_users
from mischief.schema import UserSchema, AuthenticationSchema, EmailSchema, UserImageSchema, SectionSchema, MentorSchema, MenteeSchema, FeedbackSchema
from mischief.util import mongo, mg
from mischief.util.decorators import use_args_with


def update_successful(update):
    return update.acknowledged and update.modified_count == 1

def delete_successful(delete):
    return delete.acknowledged and delete.deleted_count == 1

user_schema = UserSchema()
users_schema = UserSchema(many=True)
section_schema = SectionSchema()
sections_schema = SectionSchema(many=True)


class MischiefView(FlaskView):
    base_args = ['data']

class UsersView(MischiefView):
    """user API endpoints"""

    @use_args_with(UserSchema)
    def post(self, data):
        i = mongo.db.users.insert_one(data)
        if i.acknowledged:
            return user_schema.dump(user_by_id(i.inserted_id))
        else:
            abort(500, 'Failed to insert document')

    @jwt_required
    def index(self):
        return users_schema.dump(mongo.db.users.find())

    @jwt_required
    def get(self, user_id):
        return user_schema.dump(user_by_id(user_id, error=True))

    @use_args_with(UserSchema)
    @jwt_required
    def patch(self, data, user_id):
        u = mongo.db.users.update_one({'_id': user_id},
                                      {'$set': data})
        if update_successful(u):
            user = user_by_id(user_id)
            return user_schema.dump(user)
        else:
            abort(500, 'Failed to update document')

    @jwt_required
    def delete(self, user_id):
        d = mongo.db.users.delete_one({'_id': user_id})
        if delete_successful(d):
            return {'success': True}
        else:
            abort(500, 'Failed to delete document')

    @route('/<user_id>/set_image', methods=['POST'])
    @use_args_with(UserImageSchema, locations=('files',))
    @jwt_required
    def set_image(self, data, user_id):
        user_by_id(user_id, error=True)
        # TODO: refactor this into an s3 module
        bucket = boto3.resource('s3').Bucket('lemming-user-images')
        response = bucket.put_object(Key=str(user_id), Body=data['image'],\
            ContentType=data['image'].content_type)
        if response.e_tag is not None:
            url = boto3.client('s3').generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': 'lemming-user-images',
                    'Key': str(user_id)
                })
            mongo.db.users.update_one({'_id': user_id},
                                      {'$set': {'image': url}})
            return {'image': url}
        else:
            abort(500, 'Failed to upload resource')


class ActivationView(MischiefView):
    """user account activation endpoints"""
    @use_args_with(EmailSchema)
    def post(self, data):
        user = mongo.db.users.find_one_or_404({'email': data['email']})
        token = jwt.encode(data, user['password'])
        url = url_for('ActivationView:get', token=str(token, 'utf8'), _external=True)
        html = '<a href="{}">click here!</a>'.format(url)
        res = mg.send(to=data['email'], content=html, subject='activate your lemming account')
        return {'success': res.status_code == 200}, res.status_code

    @route('/<string:token>')
    def get(self, token):
        payload = jwt.decode(token.encode('utf8'), verify=False)
        user = mongo.db.users.find_one_or_404({'email': payload['email']})
        if not jwt.decode(token, user['password']):
            abort(401, 'Failed to verify token')
        u = mongo.db.users.update_one({'email': payload['email']},
                                      {'$set': {'is_enabled': True}})
        if update_successful(u):
            return 'enabled! ヽ(´ᗜ｀)ノ'
        else:
            abort(500, 'Failed to update document')


class AuthenticationView(MischiefView):
    """user token auth endpoint"""
    @use_args_with(AuthenticationSchema)
    def post(self, data):
        password = data.pop('password')
        user = mongo.db.users.find_one_or_404(data)
        if user.get('is_enabled') and checkpw(password.encode('utf8'), user['password']):
            return {'token': create_jwt(str(user['_id']))}
        else:
            abort(401, 'Failed to authorize')

    @route('/reset', methods=['POST'])
    @use_args_with(EmailSchema)
    @jwt_required
    def reset(self, data):
        user = mongo.db.users.find_one_or_404({'email': data['email']})
        token = jwt.encode(data, user['password'])
        url = url_for('AuthenticationView:new_password', token=str(token, 'utf8'), _external=True)
        html = '<a href="{}">click here!</a>'.format(url)
        res = mg.send(to=data['email'], content=html, subject='reset your lemming password')
        return {'success': res.status_code == 200}, res.status_code

    @route('/<string:token>')
    @jwt_required
    def new_password(self, token):
        payload = jwt.decode(token, verify=False)
        user = mongo.db.users.find_one_or_404({'email': payload['email']})
        if not jwt.decode(token, user['password']):
            abort(400, 'Failed to verify token')
        return 'ᕕ(ᐛ)ᕗ', 303


class SectionsView(MischiefView):
    """section API endpoints"""
    decorators = [jwt_required]

    @use_args_with(SectionSchema)
    def post(self, data):
        i = mongo.db.sections.insert_one(data)
        if i.acknowledged:
            return section_schema.dump(section_by_id(i.inserted_id))
        else:
            abort(500, 'Failed to insert document')

    def index(self):
        return sections_schema.dump(mongo.db.sections.find())

    def get(self, section_id):
        return section_schema.dump(section_by_id(section_id, error=True))

    @use_args_with(SectionSchema)
    def patch(self, data, section_id):
        u = mongo.db.sections.update_one({'_id': section_id},
                                         {'$set': data})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500, 'Failed to update document')

    def delete(self, section_id):
        d = mongo.db.sections.delete_one({'_id': section_id})
        if delete_successful(d):
            return {'success': True}
        else:
            abort(500, 'Failed to delete document')

    @route('/<section_id>/mentors')
    def mentors(self, section_id):
        return mongo.db.sections.find_one_or_404({'_id': section_id},
                                                 projection=['mentors'])

    @route('/<section_id>/mentors', methods=['POST'])
    @use_args_with(MentorSchema)
    def add_mentors(self, data, section_id):
        if 'mentor_id' in data:
            op = {'mentors': embed_user(data['mentor_id'], error=True)}
        elif 'mentor_ids' in data:
            op = {'mentors': {'$each': embed_users(data['mentor_ids'], error=True)}}
        else:
            abort(400, 'Failed to provide mentor_id or mentor_ids')
        u = mongo.db.sections.update_one({'_id': section_id},
                                         {'$push': op})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500, 'Failed to update document')

    @route('/<section_id>/mentors/<mentor_id>/feedback', methods=['POST'])
    @use_args_with(FeedbackSchema)
    def add_feedback(self, data, section_id, mentor_id):
        if 'body' not in data:
            abort(400, 'Failed to include feedback body')
        u = mongo.db.sections.update_one({'_id': section_id, 'mentors._id': mentor_id},
                                         {'$push': {'mentors.$.feedback': data['body']}})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500, 'Failed to update document')

    @route('/<section_id>/mentors/<mentor_id>/feedback', methods=['DELETE'])
    def clear_feedback(self, section_id, mentor_id):
        u = mongo.db.sections.update_one({'_id': section_id, 'mentors._id': mentor_id},
                                         {'$unset': {'mentors.$.feedback': ''}})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500, 'Failed to update document')

    @route('/<section_id>/mentees')
    def mentees(self, section_id):
        return mongo.db.sections.find_one_or_404({'_id': section_id},
                                                 projection=['mentees'])

    @route('/<section_id>/mentees', methods=['POST'])
    @use_args_with(MenteeSchema)
    def add_mentees(self, data, section_id):
        if 'mentee_id' in data:
            op = {'mentees': embed_user(data['mentee_id'], error=True)}
        elif 'mentee_ids' in data:
            op = {'mentees': {'$each': embed_users(data['mentee_ids'], error=True)}}
        else:
            abort(400, 'Failed to provide mentee_id or mentee_ids')
        u = mongo.db.sections.update_one({'_id': section_id},
                                         {'$push': op})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500, 'Failed to update document')
