from flask_classful import FlaskView

class BaseView(FlaskView):
  # base view to add default parameter
  base_args = ['args']
  # this will prevent flask_classful from
  # adding an "<args>" parameter to the URL
