from peewee import Model

from mischief.util import db

class Base(Model):
  class Meta:
    database = db

