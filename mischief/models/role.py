from peewee import ForeignKeyField, CharField

from mischief.models.base import Base
from mischief.models.user import User
from mischief.models.group import Group

class Role(Base):
  user = ForeignKeyField(User)
  group = ForeignKeyField(Group)
  title = CharField()
  location_classroom = CharField()

  class Meta:
    indexes = (
      (('user', 'group'), True),
    )
