from mischief import app

app.config.from_object('mischief.dev.config.Config')
app.run(host='0.0.0.0', port=5050, debug=True, threaded=True)
