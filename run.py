import os

from mischief import app

os.environ['MISCHIEF_CONFIG'] = 'mischief/config.cfg'
app.run(host='0.0.0.0', port=5050, debug=True, threaded=True)
