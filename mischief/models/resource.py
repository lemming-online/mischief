from peewee import CharField, ForeignKeyField

from mischief.models.base import Base
from mischief.models.group import Group

class Resource(Base):
  url = CharField(unique=True)
  title = CharField()
  description = CharField()
  group = ForeignKeyField(Group)

