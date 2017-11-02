# -*- coding: utf-8 -*-
"""
REST resource views
"""
import boto3
import jwt
import pprint
from bson import ObjectId
from bcrypt import checkpw
from flask import abort, url_for
from flask_classful import FlaskView, route
from flask_jwt_simple import create_jwt
from webargs import fields
from webargs.flaskparser import use_args

from mischief.mongo import user_by_id, section_by_id, embed_user, embed_users
from mischief.schema import UserSchema, AuthenticationSchema, EmailSchema, UserImageSchema, SectionSchema
from mischief.util import mongo, mg, fredis
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
            abort(500)

    def index(self):
        return users_schema.dump(mongo.db.users.find())

    def get(self, user_id):
        return user_schema.dump(user_by_id(user_id, error=True))

    @use_args_with(UserSchema)
    def patch(self, data, user_id):
        u = mongo.db.users.update_one({'_id': user_id},
                                      {'$set': data})
        if update_successful(u):
            user = user_by_id(user_id)
            return user_schema.dump(user)
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


class SectionsView(MischiefView):
    """section API endpoints"""

    @use_args_with(SectionSchema)
    def post(self, data):
        i = mongo.db.sections.insert_one(data)
        if i.acknowledged:
            return section_schema.dump(section_by_id(i.inserted_id))
        else:
            abort(500)

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
            abort(500)

    def delete(self, section_id):
        d = mongo.db.sections.delete_one({'_id': section_id})
        if delete_successful(d):
            return {'success': True}
        else:
            abort(500)

    @route('/<section_id>/mentors')
    def mentors(self, section_id):
        return users_schema.dump(mongo.db.sections.find_one_or_404({'_id': section_id},
                                                                   projection=['mentors']))

    @route('/<section_id>/mentors', methods=['POST'])
    def add_mentors(self, data, section_id):
        if 'mentor_id' in data:
            op = {'mentors': embed_user(data['mentor_id'])}
        elif 'mentor_ids' in data:
            op = {'mentors': {'$each': embed_users(data['mentor_ids'])}}
        else:
            abort(400)
        u = mongo.db.sections.update_one({'_id': section_id},
                                         {'$push': op})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500)

    @route('/<section_id>/mentees')
    def mentors(self, section_id):
        return users_schema.dump(mongo.db.sections.find_one_or_404({'_id': section_id},
                                                                   projection=['mentees']))

    @route('/<section_id>/mentees', methods=['POST'])
    def add_mentors(self, data, section_id):
        if 'mentee_id' in data:
            op = {'mentees': embed_user(data['mentee_id'])}
        elif 'mentee_ids' in data:
            op = {'mentees': {'$each': embed_users(data['mentee_ids'])}}
        else:
            abort(400)
        u = mongo.db.sections.update_one({'_id': section_id},
                                         {'$push': op})
        if update_successful(u):
            section = section_by_id(section_id)
            return section_schema.dump(section)
        else:
            abort(500)

class SessionsView(MischiefView):
    """Sessions API endpoints"""

    def index(self):
        return {'sessions': list(fredis.smembers('sessions'))}

    def get(self, section_id):
        return fredis.hgetall('session:' + str(section_id))

    @use_args({'section_id': fields.Str()})
    def post(self, data):
        # Create new session
        section_id = data['section_id']
        name_session = 'session:' + str(section_id)
        name_queue = 'queue:' + str(section_id)  
        
        if fredis.exists(name_session):
            abort(500, 'Session already exists')

        res = fredis.hmset('session:' + section_id, {'num_tickets': 0, 'helped_tickets': 0})

        if res:
            fredis.sadd('sessions', section_id)

            return fredis.hgetall('session:' + section_id)
        else:
            abort(500, 'Failed to create session')

    def delete(self, section_id):
        # End session and archive
        name_session = 'session:' + str(section_id)
        name_queue = 'queue:' + str(section_id)
        name_question = 'question:' + str(section_id) + ':'

        session_data = fredis.hgetall('session:' + str(section_id))

        question_list = []

        count = 1
        while(count <= int(session_data['num_tickets'])):
            question_data = fredis.hgetall(name_question + str(count))           

            if question_data != None:
                question_archive = {
                    'user': embed_user(ObjectId(question_data['user'])),
                    'question': question_data['question'],
                    'helped': question_data['helped'],
                    'session': ObjectId(section_id)
                }

                i = mongo.db.questions.insert_one(question_archive)
                
                if i.acknowledged:
                    question_list.append(i.inserted_id)
                    fredis.delete(name_question + str(count))
                else:
                    abort(500, 'Failed to close session')
                
                count = count + 1

        session_archive = {
            'section': ObjectId(section_id),
            'tickets': session_data['num_tickets'],
            'tickets_helped': session_data['helped_tickets'],
            'questions': question_list
        }

        i = mongo.db.sessions.insert_one(session_archive)

        if i.acknowledged:
            fredis.delete(name_session)
            fredis.srem('sessions', section_id)
            fredis.delete(name_queue)

            return {'success': True}
        else:
            abort(500, 'Failed to close session')
  
    @route('/<section_id>/add', methods=['POST'])
    @use_args({'user': fields.Str(required=True), 'question': fields.Str(required=True)})
    def add_queue(self, data, section_id):
        # Add user to queue
        name_queue = 'queue:' + str(section_id)
        name_session = 'session:' + str(section_id)
        name_user = 'users:' + str(section_id)
        
        if fredis.zrank(name_queue, data['user']) != None:
            abort(500, 'User already in queue')

        #TODO: Determine algorithm for score
        res = fredis.zadd(name_queue, 1.0, data['user'])        

        if res:
            question_num = fredis.hincrby(name_session, 'num_tickets', 1)
            name_question = 'question:' + str(section_id) + ':' + str(question_num)
            fredis.hmset(name_question, {'user': data['user'], 'question': data['question'], 'helped': False})
  
            fredis.hmset(name_user, {data['user']: question_num})

            position = fredis.zrank(name_queue, data['user'])

            return {'position': position + 1}
        else:
            abort(500, 'Failed to add to queue')

    @route('/<section_id>/remove', methods=['DELETE'])
    def remove_queue(self, section_id):
        # Remove user with highest priority from queue
        name_queue = 'queue:' + str(section_id)
        name_session = 'session:' + str(section_id)
        name_user = 'users:' + str(section_id)

        user = fredis.zrange(name_queue, 0, 0)
        question_num = fredis.hget(name_user, user[0])
        name_question = 'question:' + str(section_id) + ':' + str(question_num)
        
        res = fredis.zremrangebyrank(name_queue, 0, 0)
        
        if res:
            fredis.hincrby(name_session, 'helped_tickets', 1)
            fredis.hmset(name_question, {'helped': True})

            return {'success': True}
        else:
            abort(500, 'Failed to remove from queue')

    @route('/<section_id>/remove/<user_id>', methods=['DELETE'])
    def remove_queue_student(self, section_id, user_id):
        # Remove specific user from queue
        name_queue = 'queue:' + str(section_id)
        name_session = 'session:' + str(section_id)
        name_user = 'users:' + str(section_id)

        question_num = fredis.hget(name_user, str(user_id))
        name_question = 'question:' + str(section_id) + ':' + str(question_num)     

        res = fredis.zrem(name_queue, str(user_id))
        
        if res:
            fredis.hincrby(name_session, 'helped_tickets', 1)
            fredis.hmset(name_question, {'helped': True})

            return {'success': True}
        else:
            abort(500, 'Failed to remove from queue')

    @route('/<section_id>/queue/<user_id>')
    def get_position(self, section_id, user_id):
        # Get user's position in queue
        name_queue = 'queue:' + str(section_id)

        res = fredis.zrank(name_queue, str(user_id))
        
        if res == None:  
            abort(500, 'Failed to get position')
        else:
            return {'rank': res + 1}