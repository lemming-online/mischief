from playhouse.postgres_ext import JSONField, ForeignKeyField

from mischief.models.base import Base
from mischief.models.group import Group

class SessionArchive(Base):
  group = ForeignKeyField(Group)
  data = JSONField()
