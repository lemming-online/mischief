from peewee import CharField

from mischief.models.base import Base

class Group(Base):
  name = CharField(unique=True)
  location = CharField()
  description = CharField()
  website = CharField()
