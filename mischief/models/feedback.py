from peewee import ForeignKeyField, CharField

from mischief.models.base import Base
from mischief.models.user import User
from mischief.models.group import Group

class Feedback(Base):
  user = ForeignKeyField(User)
  group = ForeignKeyField(Group)
  body = CharField()

  class Meta:
    indexes = (
      (('user', 'group'), False),
    )
