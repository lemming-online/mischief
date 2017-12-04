import os

from mischief import create_app, socketio

os.environ['MISCHIEF_CONFIG'] = 'config.cfg'
socketio.run(create_app(), host='0.0.0.0', port=5050, debug=True)
