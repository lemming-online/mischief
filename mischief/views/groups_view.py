from flask_classful import route
from flask_jwt_simple import jwt_required, get_jwt_identity, create_jwt
from playhouse.shortcuts import model_to_dict
from webargs import fields
from webargs.flaskparser import use_args

from mischief.models.group import Group
from mischief.models.user import User
from mischief.models.user_groups import UserGroups
from mischief.views.base_view import BaseView

class GroupsView(BaseView):
  # handle groups

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
    UserGroups.create(user=current_user, group=group, title='mentor')
    return model_to_dict(group)

  @use_args({
    'name': fields.Str(required=True),
    'location': fields.Str(required=True),
    'description': fields.Str(required=True),
    'website': fields.Str(required=True),
  })
  def put(self, args, group_id):
    # update a group, if the current user is a mentor
    pass

  @route('/<group_id>/people')
  def people(self, group_id):
    # get the people associated with a group, as well as their roles
    pass

  @route('/<group_id>/people', methods=['POST'])
  @use_args({
    'user_id': fields.Integer(required=True),
    'role': fields.Str(required=True, choices=['mentor', 'mentee'])
  })
  def add_person(self, args, group_id):
    # add a new person to the group, if the current user is a mentor
    pass

  @route('/<group_id>/resources')
  def resources(self, group_id):
    # get the resources associated with a group
    pass

  @route('/<group_id>/resources', methods=['POST'])
  @use_args({})
  def add_resource(self, args, group_id):
    # add a new resource to the group, if the current user is a mentor
    pass

