from peewee import CharField, BooleanField

from mischief.models.base import Base

class User(Base):
  first_name = CharField()
  last_name = CharField()
  email = CharField(unique=True)
  encrypted_password = CharField()
  is_enabled = BooleanField(default=False)
  image = CharField(default='')
