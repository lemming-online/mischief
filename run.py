import os

from mischief import create_app

os.environ['MISCHIEF_CONFIG'] = 'config.cfg'
create_app().run(host='0.0.0.0', port=5050, debug=True, threaded=True)
