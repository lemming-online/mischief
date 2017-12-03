from bcrypt import hashpw, gensalt, checkpw
from flask import request
from flask_classful import route
from flask_jwt_simple import jwt_required, get_jwt_identity, create_jwt
from playhouse.shortcuts import model_to_dict
from webargs import fields
from webargs.flaskparser import use_args

from mischief.models.group import Group
from mischief.models.user import User
from mischief.models.user_groups import UserGroups
from mischief.views.base_view import BaseView

class UsersView(BaseView):
  # handle user accounts

  @jwt_required
  def index(self):
    # get the current user's account info and group membership
    user_email = get_jwt_identity()
    return {
      'user': model_to_dict(User.get(User.email == user_email), exclude=[User.encrypted_password]),
      'groups': [g for g in Group
                .select(Group, UserGroups)
                .join(UserGroups)
                .join(User)
                .where(User.email == user_email)
                .dicts()],
    }

  @jwt_required
  def get(self, user_id):
    # get the account info of an arbitrary user
    return model_to_dict(User.get(User.id == user_id), exclude=[User.encrypted_password])

  @use_args({
    'first_name': fields.Str(required=True),
    'last_name': fields.Str(required=True),
    'email': fields.Str(required=True),
    'password': fields.Str(required=True),
  })
  def post(self, args):
    # register a new user account
    encrypted_password = hashpw(args.pop('password').encode('utf8'), gensalt())
    args['encrypted_password'] = encrypted_password
    return model_to_dict(User.create(**args), exclude=[User.encrypted_password])

  @jwt_required
  @use_args({
    'first_name': fields.Str(required=True),
    'last_name': fields.Str(required=True),
    'email': fields.Str(required=True),
  })
  def put(self, args):
    # update the current user's account info
    user_email = get_jwt_identity()
    rows = User.update(**args).where(User.email == user_email)
    if rows == 1:
      return model_to_dict(User.get(User.email == user_email))
    else:
      abort('500', 'Failed to update user')

  @route('/activation', methods=['POST'])
  def start_activation(self):
    # prompt the account activation process and send an email
    pass

  @route('/activation/<string:token>')
  def complete_activation(self, token):
    # resolve the account activation process and update the user's status
    pass

  @use_args({
    'email': fields.Str(required=True),
    'password': fields.Str(required=True),
  })
  def login(self, args):
    # generate a login token for a user, given valid credentials
    user = User.get(User.email == args['email'])
    if checkpw(args['password'].encode('utf8'), user.encrypted_password.encode('utf8')):
      return {'token': create_jwt(user.id)}
    else:
      abort(401, 'Unauthorized')

  @route('/reset', methods=['POST'])
  def start_reset_password(self):
    # prompt the password reset process and send an email
    pass

  @route('/reset/<string:token>')
  def complete_reset_password(self, token):
    # resolve password reset process and update the user's password
    pass
