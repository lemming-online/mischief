from eve import Eve
from eve_auth_jwt import JWTAuth
from flask.ext.mail import Mail

app = Eve(auth=JWTAuth)
mail = Mail(app)
