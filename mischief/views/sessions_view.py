from flask_classful import route
from flask_jwt_simple import jwt_required
from webargs import fields
from webargs.flaskparser import use_args

from mischief.views.base_view import BaseView
from mischief.util import fredis

class SessionsView(BaseView):
    # section handling

    decorators = [jwt_required]

    def index(self):
        # List of active sessions
        return {'sessions': list(fredis.smembers('sessions'))}

    def get(self, group_id):
        #TODO: Build this out to return more data about a session
        return {'session': fredis.hgetall('session:' + str(group_id))}

    @use_args({
      'group_id': fields.Str(required=True),
    })
    def post(self, args):
        # Create new session
        group_id = args['group_id']
        name_session = 'session:' + str(group_id)
        name_queue = 'queue:' + str(group_id)

        if fredis.exists(name_session):
            abort(500, 'Session already exists')

        res = fredis.hmset('session:' + group_id, {'num_tickets': 0, 'helped_tickets': 0})

        if res:
            fredis.sadd('sessions', group_id)

            return fredis.hgetall('session:' + group_id)
        else:
            abort(500, 'Failed to create session')

    def delete(self, group_id):
        # End session and archive
        name_session = 'session:' + str(group_id)
        name_queue = 'queue:' + str(group_id)
        name_announcements = 'announcements:' + str(group_id)
        name_faq = 'faq:' + str(group_id)
        name_user = 'users:' + str(group_id)

        session_data = fredis.hgetall('session:' + str(group_id))
        announcement_data = fredis.lrange(name_announcements, 0, -1)
        faq_data = fredis.lrange(name_faq, 0, -1)

        question_list = []

        count = 1

        while(count <= int(session_data['num_tickets'])):
            name_question = 'question:' + str(group_id) + ':' + str(count)
            question_data = fredis.hgetall(name_question)

            if question_data != None:
                question_archive = {
                    'user': embed_user(ObjectId(question_data['user'])),
                    'question': question_data['question'],
                    'helped': question_data['helped'],
                    'session': ObjectId(group_id)
                }

                i = mongo.db.questions.insert_one(question_archive)

                if i.acknowledged:
                    question_list.append(i.inserted_id)
                    fredis.delete(name_question)
                else:
                    abort(500, 'Failed to close session')

                count = count + 1

        session_archive = {
            'group_id': group_id,
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
            fredis.srem('sessions', group_id)

            return {'success': True}
        else:
            abort(500, 'Failed to close session')

    @route('/<group_id>/add', methods=['POST'])
    @use_args({'user': fields.Str(required=True), 'question': fields.Str(required=True)})
    def add_queue(self, data, group_id):
        # Add user to queue
        name_queue = 'queue:' + str(group_id)
        name_session = 'session:' + str(group_id)
        name_user = 'users:' + str(group_id)

        if fredis.zrank(name_queue, data['user']) != None:
            abort(500, 'User already in queue')

        #TODO: Determine algorithm for score
        res = fredis.zadd(name_queue, 1.0, data['user'])

        if res:
            question_num = fredis.hincrby(name_session, 'num_tickets', 1)
            name_question = 'question:' + str(group_id) + ':' + str(question_num)
            fredis.hmset(name_question, {'user': data['user'], 'question': data['question'], 'helped': False})

            fredis.hmset(name_user, {data['user']: question_num})

            position = fredis.zrank(name_queue, data['user'])

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
            return {'success': True}
        else:
            abort(500, 'Announcement failed to post')

    @route('/<group_id>/announcements', methods=['DELETE'])
    def clear_announcements(self, group_id):
        # Clear announcements from a session
        name_announcements = 'announcements:' + str(group_id)

        res = fredis.delete(name_announcements)

        if res:
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
    def add_faq(self, data, group_id):
        # Add a FAQ
        name_faq = 'faq:' + str(group_id)

        res = fredis.lpush(name_faq, data['answer'], data['question'])

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
            abort(500, 'Failed to retrieve queue')

    @route('/<group_id>/queue/<user_id>')
    def get_position(self, group_id, user_id):
        # Get user's position in queue
        name_queue = 'queue:' + str(group_id)

        res = fredis.zrank(name_queue, str(user_id))

        if res == None:
            abort(500, 'Failed to get position')
        else:
            return {'rank': res + 1}
