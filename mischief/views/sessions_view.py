import time
import datetime

from flask import abort
from flask_classful import route
from flask_jwt_simple import jwt_required, get_jwt
from webargs import fields
from webargs.flaskparser import use_args
from playhouse.shortcuts import model_to_dict
from flask_socketio import join_room, leave_room, emit, send

from mischief import socketio
from mischief.models.user import User
from mischief.models.group import Group
from mischief.models.session_archive import SessionArchive
from mischief.views.base_view import BaseView
from mischief.util import fredis

class SessionsView(BaseView):
    # Group Handling

    decorators = [jwt_required]

    def index(self):
        # List of active sessions
        return {'sessions': list(fredis.smembers('sessions'))}

    def get(self, group_id):
        # Get session information
        name_session = 'session:' + str(group_id)

        if fredis.exists(name_session) == False:
            abort(500, 'Session does not exist')

        session = fredis.hgetall(name_session)
        queue = fredis.zrangebyscore('queue:' + str(group_id), '-inf', '+inf')
        announcements = fredis.lrange('announcements:' + str(group_id), 0, -1)
        faqs = fredis.lrange('faq:' + str(group_id), 0, -1)

        return {
            'session': session,
            'queue': queue,
            'announcements': announcements,
            'faqs': [tuple(faqs[i:i+2]) for i in range(0, len(faqs), 2)]
        }

    @use_args({'group_id': fields.Str(), 'title': fields.Str()})
    def post(self, args):
        # Create new session
        group_id = args['group_id']
        title = args['title']
        name_session = 'session:' + str(group_id)
        name_queue = 'queue:' + str(group_id)

        if fredis.exists(name_session):
            abort(500, 'Session already exists')

        res = fredis.hmset('session:' + group_id, {'title': title, 'num_tickets': 0, 'helped_tickets': 0})

        if res:
            fredis.sadd('sessions', group_id)

            session = fredis.hgetall(name_session)
            queue = fredis.zrangebyscore('queue:' + str(group_id), '-inf', '+inf')
            announcements = fredis.lrange('announcements:' + str(group_id), 0, -1)
            faqs = fredis.lrange('faq:' + str(group_id), 0, -1)

            return {
                'session': session,
                'queue': queue,
                'announcements': announcements,
                'faqs': [tuple(faqs[i:i+2]) for i in range(0, len(faqs), 2)]
            }
        else:
            abort(500, 'Failed to create session')

    def delete(self, group_id):
        # End session and archive
        name_session = 'session:' + str(group_id)
        name_queue = 'queue:' + str(group_id)
        name_announcements = 'announcements:' + str(group_id)
        name_faq = 'faq:' + str(group_id)
        name_user = 'users:' + str(group_id)

        if fredis.exists(name_session) == False:
            abort(500, 'Session does not exist')

        session_data = fredis.hgetall('session:' + str(group_id))
        announcement_data = fredis.lrange(name_announcements, 0, -1)
        faq_data = fredis.lrange(name_faq, 0, -1)

        question_list = []

        count = 1
        total_time = 0

        while(count <= int(session_data['num_tickets'])):
            name_question = 'question:' + str(group_id) + ':' + str(count)
            question_data = fredis.hgetall(name_question)

            if question_data != None:
                question_archive = {
                    'user': model_to_dict(User.get(User.id == question_data['user']), exclude=[User.encrypted_password]),
                    'question': question_data['question'],
                    'helped': question_data['helped'],
                    'helped_time': question_data['helped_time']
                }

                question_list.append(question_archive)
                fredis.delete(name_question)

                if bool(question_archive['helped']) == True:
                    total_time = total_time + int(question_archive['helped_time'])

                count = count + 1

        average_response_time = (total_time/(count-1)) if count > 1 else 0

        session_archive = {
            'group': model_to_dict(Group.get(Group.id == group_id)),
            'title': session_data['title'],
            'tickets': session_data['num_tickets'],
            'tickets_helped': session_data['helped_tickets'],
            'questions': question_list,
            'announcements': announcement_data,
            'faqs': [tuple(faq_data[i:i+2]) for i in range(0, len(faq_data), 2)],
            'average_response_time': average_response_time,
            'date': str(datetime.date.today())
        }

        archive = SessionArchive.create(data=session_archive, group_id=group_id)

        fredis.delete(name_session)
        fredis.delete(name_user)
        fredis.delete(name_announcements)
        fredis.delete(name_faq)
        fredis.delete(name_queue)
        fredis.srem('sessions', group_id)

        sessions = SessionArchive.select().join(Group).where(Group.id == group_id).order_by(SessionArchive.id.desc())

        list_archived = []

        for s in sessions:
            list_archived.append(model_to_dict(s))

        

        return list_archived

    @route('/<group_id>/archived')
    def get_archived_sessions(self, group_id):
        # Get session information
        sessions = SessionArchive.select().join(Group).where(Group.id == group_id).order_by(SessionArchive.id.desc())

        list_archived = []

        for s in sessions:
            list_archived.append(model_to_dict(s))

        return list_archived

    @route('/<group_id>/add', methods=['POST'])
    @use_args({'user': fields.Str(required=True), 'question': fields.Str(required=True)})
    def add_queue(self, args, group_id):
        # Add user to queue
        name_queue = 'queue:' + str(group_id)
        name_session = 'session:' + str(group_id)
        name_user = 'users:' + str(group_id)

        if fredis.zrank(name_queue, args['user']) != None:
            abort(500, 'User already in queue')

        res = fredis.zadd(name_queue, time.time(), args['user'])

        if res:
            question_num = fredis.hincrby(name_session, 'num_tickets', 1)
            name_question = 'question:' + str(group_id) + ':' + str(question_num)
            fredis.hmset(name_question, {'user': args['user'], 'question': args['question'], 'helped': False, 'helped_time': int(round(time.time()))})

            fredis.hmset(name_user, {args['user']: question_num})

            position = fredis.zrank(name_queue, args['user'])

            socketio.emit('queue', {'queue': fredis.zrangebyscore(name_queue, '-inf', '+inf')}, room=str(group_id))

            return {'position': position + 1}
        else:
            abort(500, 'Failed to add to queue')

    @route('/<group_id>/remove', methods=['DELETE'])
    def remove_queue(self, group_id):
        # Remove user with highest priority from queue
        name_queue = 'queue:' + str(group_id)
        name_session = 'session:' + str(group_id)
        name_user = 'users:' + str(group_id)

        user = fredis.zrange(name_queue, 0, 0)
        question_num = fredis.hget(name_user, user[0])
        name_question = 'question:' + str(group_id) + ':' + str(question_num)

        res = fredis.zremrangebyrank(name_queue, 0, 0)

        if res:
            fredis.hincrby(name_session, 'helped_tickets', 1)
            fredis.hmset(name_question, {'helped': True})

            start_time = int(fredis.hget(name_question, 'helped_time'))
            elapsed_time = int(round(time.time())) - start_time
            fredis.hmset(name_question, {'helped_time': elapsed_time })

            socketio.emit('queue', {'queue': fredis.zrangebyscore(name_queue, '-inf', '+inf')}, room=str(group_id))

            return {'success': True}
        else:
            abort(500, 'Failed to remove from queue')

    @route('/<group_id>/remove/<user_id>', methods=['DELETE'])
    def remove_queue_student(self, group_id, user_id):
        # Remove specific user from queue
        name_queue = 'queue:' + str(group_id)
        name_session = 'session:' + str(group_id)
        name_user = 'users:' + str(group_id)

        question_num = fredis.hget(name_user, str(user_id))
        name_question = 'question:' + str(group_id) + ':' + str(question_num)

        res = fredis.zrem(name_queue, str(user_id))

        if res:
            fredis.hincrby(name_session, 'helped_tickets', 1)
            fredis.hmset(name_question, {'helped': True})

            start_time = int(fredis.hget(name_question, 'helped_time'))
            elapsed_time = int(round(time.time())) - start_time
            fredis.hmset(name_question, {'helped_time': elapsed_time })

            socketio.emit('queue', {'queue': fredis.zrangebyscore(name_queue, '-inf', '+inf')}, room=str(group_id))

            return {'success': True}
        else:
            abort(500, 'Failed to remove from queue')

    @route('/<group_id>/cancel/<user_id>', methods=['DELETE'])
    def cancel_queue_student(self, group_id, user_id):
        # Cancel a specific user from queue
        name_queue = 'queue:' + str(group_id)
        name_session = 'session:' + str(group_id)
        name_user = 'users:' + str(group_id)

        question_num = fredis.hget(name_user, str(user_id))
        name_question = 'question:' + str(group_id) + ':' + str(question_num)

        res = fredis.zrem(name_queue, str(user_id))

        if res:
            socketio.emit('queue', {'queue': fredis.zrangebyscore(name_queue, '-inf', '+inf')}, room=str(group_id))

            return {'success': True}
        else:
            abort(500, 'Failed to remove from queue')

    @route('/<group_id>/announcements')
    def get_announcements(self, group_id):
        # Get all announcements from a session
        name_announcements = 'announcements:' + str(group_id)

        return {'announcements': fredis.lrange(name_announcements, 0, -1)}

    @route('/<group_id>/announcements', methods=['POST'])
    @use_args({'announcement': fields.Str(required=True)})
    def add_announcement(self, data, group_id):
        # Add an announcement to a session
        name_announcements = 'announcements:' + str(group_id)

        res = fredis.lpush(name_announcements, data['announcement'])

        if res:
            socketio.emit('announcements', {'announcements': fredis.lrange(name_announcements, 0, -1)}, room=str(group_id))

            return {'success': True}
        else:
            abort(500, 'Announcement failed to post')

    @route('/<group_id>/announcements', methods=['DELETE'])
    def clear_announcements(self, group_id):
        # Clear announcements from a session
        name_announcements = 'announcements:' + str(group_id)

        res = fredis.delete(name_announcements)

        if res:
            socketio.emit('announcements', {'announcements': []})

            return {'success': True}
        else:
            abort(500, 'Failed to delete announcements')


    @route('/<group_id>/faq')
    def get_faqs(self, group_id):
        # Get all FAQs from a session
        name_faq = 'faq:' + str(group_id)

        faqs = fredis.lrange(name_faq, 0, -1)
        return {'faqs': [tuple(faqs[i:i+2]) for i in range(0, len(faqs), 2)]}

    @route('/<group_id>/faq', methods=['POST'])
    @use_args({'question': fields.Str(required=True), 'answer': fields.Str(required=True)})
    def add_faq(self, args, group_id):
        # Add a FAQ
        name_faq = 'faq:' + str(group_id)

        res = fredis.lpush(name_faq, args['answer'], args['question'])

        if res:
            return {'success': True}
        else:
            abort(500, 'FAQ failed to post')

    @route('/<group_id>/faq', methods=['DELETE'])
    def clear_faqs(self, group_id):
        # Clear the FAQ list
        name_faq = 'faq:' + str(group_id)

        res = fredis.delete(name_faq)

        if res:
            return {'success': True}
        else:
            abort(500, 'Failed to delete faq')

    @route('/<group_id>/queue')
    def get_queue(self, group_id):
        # Get the entire queue
        name_queue = 'queue:' + str(group_id)

        res = fredis.zrangebyscore(name_queue, '-inf', '+inf')

        if res:
            return {'queue': res}
        else:
            abort(500, 'Empty queue')

    @route('/<group_id>/queue/<user_id>')
    def get_position(self, group_id, user_id):
        # Get user's position in queue
        name_queue = 'queue:' + str(group_id)

        res = fredis.zrank(name_queue, str(user_id))

        if res == None:
            abort(500, 'Failed to get position')
        else:
            return {'position': res + 1}
