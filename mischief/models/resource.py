from peewee import CharField, ForeignKeyField

from mischief.models.base import Base
from mischief.models.group import Group
from mischief.models.user import User

class Resource(Base):
  url = CharField(unique=True)
  title = CharField()
  description = CharField()
  group = ForeignKeyField(Group)
  user = ForeignKeyField(User)

