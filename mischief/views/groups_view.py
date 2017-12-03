from flask_classful import route
from flask_jwt_simple import jwt_required, get_jwt_identity, create_jwt, get_jwt
from playhouse.shortcuts import model_to_dict
from webargs import fields
from webargs.flaskparser import use_args

from mischief.models.feedback import Feedback
from mischief.models.group import Group
from mischief.models.resource import Resource
from mischief.models.role import Role
from mischief.models.user import User
from mischief.views.base_view import BaseView

class GroupsView(BaseView):
  # handle groups

  decorators = [jwt_required]

  def get(self, group_id):
    # return a group's details
    return model_to_dict(Group.get(Group.id == group_id))

  @use_args({
    'name': fields.Str(required=True),
    'location': fields.Str(required=True),
    'description': fields.Str(required=True),
    'website': fields.Str(required=True),
  })
  def post(self, args):
    # create a new group with the current user as the mentor
    user_email = get_jwt_identity()
    current_user = User.get(User.email == user_email)
    group = Group.create(**args)
    Role.create(user=current_user, group=group, title='mentor')
    return model_to_dict(group)

  @use_args({
    'name': fields.Str(required=True),
    'location': fields.Str(required=True),
    'description': fields.Str(required=True),
    'website': fields.Str(required=True),
  })
  def put(self, args, group_id):
    # update a group, if the current user is a mentor
    user_id = get_jwt()['uid']
    if (
      Role
        .select()
        .where(Role.user_id == user_id,
          Role.group_id == group_id,
          Role.title == 'mentor')
        .count() == 0
    ):
      abort(401, 'Not a mentor')
    group = Group.get(Group.id == group_id)
    return model_to_dict(group.update(**args))

  @route('/<group_id>/people')
  def people(self, group_id):
    # get the people associated with a group, as well as their roles
    return [u for u in User
      .select(User, Role)
      .join(Role)
      .join(Group)
      .where(Group.id == group_id)
      .dicts()]

  @route('/<group_id>/people', methods=['POST'])
  @use_args({
    'user_id': fields.Integer(required=True),
    'role': fields.Str(required=True, choices=['mentor', 'mentee'])
  })
  def add_person(self, args, group_id):
    # add a new person to the group, if the current user is a mentor
    user_id = get_jwt()['uid']
    if (
      Role
        .select()
        .where(Role.user_id == user_id,
          Role.group_id == group_id,
          Role.title == 'mentor')
        .count() == 0
    ):
      abort(401, 'Not a mentor')
    Role.create(group_id=group_id, **args)
    return model_to_dict(Group.get(Group.id == group_id))

  @route('/<group_id>/resources')
  def resources(self, group_id):
    return [r for r in Resource
      .select()
      .where(Resource.group_id == group_id)
      .dicts()]

  @route('/<group_id>/resources', methods=['POST'])
  @use_args({
    'url': fields.String(required=True),
    'title': fields.String(required=True),
    'description': fields.String(required=True),
  })
  def add_resource(self, args, group_id):
    # add a new resource to the group, if the current user is a mentor
    user_email = get_jwt_identity()
    current_user = User.get(User.email == user_email)
    return model_to_dict(Resource.create(user=current_user, group_id=group_id, **args))

  @route('/<group_id>/feedback')
  def feedback(self, group_id):
    # get the current user's feedback in a group
    user_id = get_jwt()['uid']
    return [f for f in Feedback
      .select()
      .where(Feedback.group_id == group_id, Feedback.user_id == user_id)
      .dicts()]

  @route('/<group_id>/feedback', methods=['POST'])
  @use_args({
    'user_id': fields.Integer(required=True),
    'body': fields.Str(required=True),
  })
  def add_feedback(self, args, group_id):
    # add feedback to a specific user in a specific group
    return model_to_dict(Feedback.create(group_id=group_id, **args))
