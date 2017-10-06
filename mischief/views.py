# -*- coding: utf-8 -*-
"""
REST resource views
"""
import boto3
import jwt
from bcrypt import checkpw
from flask import abort, url_for
from flask_classful import FlaskView, route
from flask_jwt_simple import create_jwt

from mischief.mongo import user_by_id, course_by_id, section_by_id
from mischief.schema import UserSchema, AuthenticationSchema, EmailSchema,\
    CourseSchema, UserImageSchema, SectionSchema
from mischief.util import mongo, mg
from mischief.util.decorators import use_args_with


def update_successful(update):
    return update.acknowledged and update.modified_count == 1

def delete_successful(delete):
    return delete.acknowledged and delete.deleted_count == 1

user_schema = UserSchema()
users_schema = UserSchema(many=True)
course_schema = CourseSchema()
courses_schema = CourseSchema(many=True)
section_schema = SectionSchema()
sections_schema = SectionSchema(many=True)


class MischiefView(FlaskView):
    base_args = ['data']

class UsersView(MischiefView):
    """user API endpoints"""
    @use_args_with(UserSchema)
    def post(self, data):
        insert = mongo.db.users.insert_one(data)
        if insert.acknowledged:
            return user_schema.dump(user_by_id(insert.inserted_id))
        else:
            abort(500)

    def index(self):
        return users_schema.dump(mongo.db.users.find())

    def get(self, user_id):
        return user_schema.dump(user_by_id(user_id, error=True))

    @use_args_with(UserSchema)
    def put(self, data, user_id):
        u = mongo.db.users.replace_one({'_id': user_id}, data)
        if update_successful(u):
            return user_schema.dump(user_by_id(user_id))
        else:
            abort(500)

    @use_args_with(UserSchema)
    def patch(self, data, user_id):
        u = mongo.db.users.update_one({'_id': user_id},
                                      {'$set': data})
        if update_successful(u):
            return user_schema.dump(user_by_id(user_id))
        else:
            abort(500)

    def delete(self, user_id):
        d = mongo.db.users.delete_one({'_id': user_id})
        if delete_successful(d):
            return {'success': True}
        else:
            abort(500)

    @route('/<user_id>/set_image', methods=['POST'])
    @use_args_with(UserImageSchema, locations=('files',))
    def set_image(self, data, user_id):
        user_by_id(user_id, error=True)
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
            abort(500)



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
            abort(400)
        u = mongo.db.users.update_one({'email': payload['email']},
                                      {'$set': {'is_enabled': True}})
        if update_successful(u):
            return 'enabled! ヽ(´ᗜ｀)ノ'
        else:
            abort(500)


class AuthenticationView(MischiefView):
    """user token auth endpoint"""
    @use_args_with(AuthenticationSchema)
    def post(self, data):
        password = data.pop('password')
        user = mongo.db.users.find_one_or_404(data)
        if user['is_enabled'] and checkpw(password.encode('utf8'), user['password']):
            return {'token': create_jwt(str(user['_id']))}
        else:
            abort(401)

    @route('/reset', methods=['POST'])
    @use_args_with(EmailSchema)
    def reset(self, data):
        user = mongo.db.users.find_one_or_404({'email': data['email']})
        token = jwt.encode(data, user['password'])
        url = url_for('AuthenticationView:new_password', token=str(token, 'utf8'), _external=True)
        html = '<a href="{}">click here!</a>'.format(url)
        res = mg.send(to=data['email'], content=html, subject='reset your lemming password')
        return {'success': res.status_code == 200}, res.status_code

    @route('/<string:token>')
    def new_password(self, token):
        payload = jwt.decode(token, verify=False)
        user = mongo.db.users.find_one_or_404({'email': payload['email']})
        if not jwt.decode(token, user['password']):
            abort(400)
        return 'ᕕ(ᐛ)ᕗ', 303



class CoursesView(MischiefView):
    """course API endpoints"""
    @use_args_with(CourseSchema)
    def post(self, data):
        insert = mongo.db.courses.insert_one(data)
        if insert.acknowledged:
            return course_schema.dump(course_by_id(insert.inserted_id))
        else:
            abort(500)

    def index(self):
        return courses_schema.dump(mongo.db.courses.find())

    def get(self, course_id):
        return course_schema.dump(course_by_id(course_id))

    @use_args_with(CourseSchema)
    def put(self, data, course_id):
        u = mongo.db.courses.replace_one({'_id': course_id}, data)
        if update_successful(u):
            return course_schema.dump(course_by_id(course_id))
        else:
            abort(500)

    @use_args_with(CourseSchema)
    def patch(self, data, course_id):
        u = mongo.db.courses.update_one({'_id': course_id},
                                        {'$set': data})
        if update_successful(u):
            return course_schema.dump(course_by_id(course_id))
        else:
            abort(500)

    def delete(self, course_id):
        d = mongo.db.courses.delete_one({'_id': course_id})
        if delete_successful(d):
            return {'success': True}
        else:
            abort(500)


class SectionsView(MischiefView):
    """section api endpoints"""
    @use_args_with(SectionSchema)
    def post(self, data):
        insert = mongo.db.sections.insert_one(data)
        if insert.acknowledged:
            return section_schema.dump(section_by_id(insert.inserted_id))
        else:
            abort(500)

    def index(self):
        return sections_schema.dump(mongo.db.sections.find())

    def get(self, section_id):
        return section_schema.dump(section_by_id(section_id, error=True))

    def put(self, data, section_id):
        u = mongo.db.sections.replace_one({'_id': section_id}, data)
        if update_successful(u):
            return section_schema.dump(section_by_id(section_id))
        else:
            abort(500)

    def patch(self, data, section_id):
        u = mongo.db.sections.update_one({'_id': section_id},
                                         {'$set': data})
        if update_successful(u):
            return section_schema.dump(section_by_id(section_id))
        else:
            abort(500)

    def delete(self, section_id):
        d = mongo.db.sections.delete_one({'_id': section_id})
        if delete_successful(d):
            return {'success': True}
        else:
            abort(500)
