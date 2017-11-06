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
from flask_jwt_simple import create_jwt, jwt_required
from webargs import fields
from webargs.flaskparser import use_args

from mischief.mongo import user_by_id, section_by_id, embed_user, embed_users
from mischief.schema import UserSchema, AuthenticationSchema, EmailSchema, UserImageSchema, SectionSchema, MentorSchema, MenteeSchema, FeedbackSchema
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
  

class SessionsView(MischiefView):
    """Sessions API endpoints"""

    def index(self):
        # List of active sessions
        return {'sessions': list(fredis.smembers('sessions'))}

    def get(self, section_id):
        #TODO: Build this out to return more data about a session
        return {'session': fredis.hgetall('session:' + str(section_id))}

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
        name_announcements = 'announcements:' + str(section_id)
        name_faq = 'faq:' + str(section_id)
        name_user = 'users:' + str(section_id)

        session_data = fredis.hgetall('session:' + str(section_id))
        announcement_data = fredis.lrange(name_announcements, 0, -1)
        faq_data = fredis.lrange(name_faq, 0, -1)

        question_list = []

        count = 1

        while(count <= int(session_data['num_tickets'])):
            name_question = 'question:' + str(section_id) + ':' + str(count)
            question_data = fredis.hgetall(name_question)        

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
                    fredis.delete(name_question)
                else:
                    abort(500, 'Failed to close session')
                
                count = count + 1

        session_archive = {
            'section': ObjectId(section_id),
            'tickets': session_data['num_tickets'],
            'tickets_helped': session_data['helped_tickets'],
            'questions': question_list,
            'announcements': announcement_data,
            'faqs': [tuple(faq_data[i:i+2]) for i in range(0, len(faq_data), 2)]
        }

        i = mongo.db.sessions.insert_one(session_archive)

        if i.acknowledged:
            fredis.delete(name_session)
            fredis.delete(name_user)
            fredis.delete(name_announcements)
            fredis.delete(name_faq)
            fredis.delete(name_queue)
            fredis.srem('sessions', section_id)

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


    @route('/<section_id>/announcements')
    def get_announcements(self, section_id):
        # Get all announcements from a session
        name_announcements = 'announcements:' + str(section_id)

        return {'announcements': fredis.lrange(name_announcements, 0, -1)}

    @route('/<section_id>/announcements', methods=['POST'])
    @use_args({'announcement': fields.Str(required=True)})
    def add_announcement(self, data, section_id):
        # Add an announcement to a session
        name_announcements = 'announcements:' + str(section_id)

        res = fredis.lpush(name_announcements, data['announcement'])

        if res:
            return {'success': True}
        else:
            abort(500, 'Announcement failed to post')

    @route('/<section_id>/announcements', methods=['DELETE'])
    def clear_announcements(self, section_id):
        # Clear announcements from a session
        name_announcements = 'announcements:' + str(section_id)

        res = fredis.delete(name_announcements)

        if res:
            return {'success': True}
        else:
            abort(500, 'Failed to delete announcements')


    @route('/<section_id>/faq')
    def get_faqs(self, section_id):
        # Get all FAQs from a session
        name_faq = 'faq:' + str(section_id)

        faqs = fredis.lrange(name_faq, 0, -1)
        return {'faqs': [tuple(faqs[i:i+2]) for i in range(0, len(faqs), 2)]}

    @route('/<section_id>/faq', methods=['POST'])
    @use_args({'question': fields.Str(required=True), 'answer': fields.Str(required=True)})
    def add_faq(self, data, section_id):
        # Add a FAQ
        name_faq = 'faq:' + str(section_id)

        res = fredis.lpush(name_faq, data['answer'], data['question'])

        if res:
            return {'success': True}
        else:
            abort(500, 'FAQ failed to post')

    @route('/<section_id>/faq', methods=['DELETE'])
    def clear_faqs(self, section_id):
        # Clear the FAQ list
        name_faq = 'faq:' + str(section_id)

        res = fredis.delete(name_faq)

        if res:
            return {'success': True}
        else:
            abort(500, 'Failed to delete faq')

    @route('/<section_id>/queue')
    def get_queue(self, section_id):
        # Get the entire queue
        name_queue = 'queue:' + str(section_id)

        res = fredis.zrangebyscore(name_queue, '-inf', '+inf')

        if res:
            return {'queue': res}
        else:
            abort(500, 'Failed to retrieve queue')

    @route('/<section_id>/queue/<user_id>')
    def get_position(self, section_id, user_id):
        # Get user's position in queue
        name_queue = 'queue:' + str(section_id)

        res = fredis.zrank(name_queue, str(user_id))
        
        if res == None:  
            abort(500, 'Failed to get position')
        else:
            return {'rank': res + 1}