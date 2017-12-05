import jwt
import os
from bcrypt import hashpw, gensalt, checkpw
from flask import request, url_for, abort, current_app
from flask_classful import route
from flask_jwt_simple import jwt_required, get_jwt_identity, create_jwt, get_jwt
from playhouse.shortcuts import model_to_dict
from PIL import Image
from webargs import fields
from webargs.flaskparser import use_args

from mischief.models.group import Group
from mischief.models.user import User
from mischief.models.role import Role
from mischief.views.base_view import BaseView
from mischief.util import mail

class UsersView(BaseView):
  # handle user accounts

  @jwt_required
  def index(self):
    # get the current user's account info and group membership
    user_id = get_jwt()['uid']
    return {
      'user': model_to_dict(User.get(User.id == user_id), exclude=[User.encrypted_password]),
      'groups': [g for g in Group
                  .select(Group, Role)
                  .join(Role, on=(Group.id == Role.group_id))
                  .where(Role.user_id == user_id)
                  .dicts()],
    }

  @jwt_required
  def get(self, user_id):
    # get the account info of an arbitrary user
    return model_to_dict(User.get(User.id == user_id), exclude=[User.encrypted_password])

  @use_args({
    'first_name': fields.Str(required=True),
    'last_name': fields.Str(required=True),
    'email': fields.Email(required=True),
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
    'email': fields.Email(required=True),
  })
  def put(self, args):
    # update the current user's account info
    user_id = get_jwt()['uid']
    user = User.get(User.id == user_id)
    user.first_name = args['first_name']
    user.last_name = args['last_name']
    user.email = args['email']
    user.save()
    return model_to_dict(user, exclude=[User.encrypted_password])

  @route('/activation', methods=['POST'])
  @use_args({
    'email': fields.Email(required=True),
  })
  def start_activation(self, args):
    # prompt the account activation process and send an email
    user = User.get(User.email == args['email'])
    token = jwt.encode({'email': user.email}, user.encrypted_password)
    url = url_for('UsersView:complete_activation', token=str(token, 'utf8'), _external=True)
    html = '<a href="{}">Click here!</a>'.format(url)
    res = mail.send(to=user.email, content=html, subject='Activate your Lemming account')
    return {'success': res.status_code == 200}, res.status_code

  @route('/activation/<string:token>')
  def complete_activation(self, token):
    # resolve the account activation process and update the user's status
    payload = jwt.decode(token.encode('utf8'), verify=False)
    user = User.get(User.email == payload['email'])
    if not jwt.decode(token, user.encrypted_password):
      abort(401, 'Failed to validate token')
    user.is_enabled = True
    user.save()
    return 'enabled! ヽ(´ᗜ｀)ノ'

  @route('/login', methods=['POST'])
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
  @use_args({
    'email': fields.Email(required=True),
  })
  def start_reset_password(self, args):
    # prompt the password reset process and send an email
    user = User.get(User.email == args['email'])
    token = jwt.encode({'email': user.email}, user.encrypted_password)
    url = url_for('UsersView:complete_reset_password', token=str(token, 'utf8'), _external=True)
    html = '<a href="{}">Click here!</a>'.format(url)
    res = mail.send(to=user.email, content=html, subject='Reset your Lemming password')
    return {'success': res.status_code == 200}, res.status_code

  @route('/reset/<string:token>')
  def complete_reset_password(self, token):
    # resolve password reset process and update the user's password
    payload = jwt.decode(token.encode('utf8'), verify=False)
    user = User.get(User.email == payload['email'])
    if not jwt.decode(token, user.encrypted_password):
      abort(401, 'Failed to validate token')
    return 'ᕕ( ᐛ )ᕗ', 303

  @route('/image', methods=['POST'])
  @jwt_required
  @use_args({
    'image': fields.Raw(required=True),
  }, locations=('files',))
  def set_image(self, args):
    # set the current user's profile image
    user_id = get_jwt()['uid']
    _, file_extension = os.path.splitext(args['image'].filename)
    path = current_app.config['UPLOAD_FOLDER'] + str(user_id) + file_extension
    args['image'].save(path)
    user = User.get(User.id == user_id)
    user.image = request.host + '/static/' + str(user_id) + file_extension
    user.save()
    return {'url': user.image}

