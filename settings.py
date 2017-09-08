import os

"""
settings for Eve
"""

# Mongo connection
MONGO_HOST = os.environ.get('MISCHIEF_MONGO_HOST', 'localhost')
MONGO_PORT = os.environ.get('MISCHIEF_MONGO_PORT', 27018)
# Mongo auth
MONGO_USERNAME = os.environ.get('MISCHIEF_MONGO_USER', '')
MONGO_PASSWORD = os.environ.get('MISCHIEF_MONGO_PASS', '')
# Mongo settings
MONGO_DBNAME = os.environ.get('MISCHIEF_MONGO_DB', 'mischief')
# Mongo uri override
MONGO_URI = os.environ.get('MISCHIEF_MONGO_URI', None)

# jwt config
JWT_SECRET = os.environ.get('MISCHIEF_JWT_SECRET', 'change me :)')
JWT_ISSUER = os.environ.get('MISCHIEF_JWT_ISSUER', 'mischief')

"""
general settings
"""

APP_EMAIL = os.environ.get('MISCHIEF_APP_EMAIL', 'lem@mischief')
