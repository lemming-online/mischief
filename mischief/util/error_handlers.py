# -*- coding: utf-8 -*-
"""
error code handlers
"""
from flask import jsonify
from pymongo.errors import DuplicateKeyError

def init_error_handlers(app):

    def generic_error(message, code):
        return jsonify({'error': {'reason': message}}), code

    def http_error(error):
        return generic_error(error.description, error.code)

    @app.errorhandler(400)
    def bad_request(error):
        return http_error(error)

    @app.errorhandler(401)
    def not_authorized(error):
        return http_error(error)

    @app.errorhandler(404)
    def not_found(error):
        return http_error(error)

    @app.errorhandler(500)
    def server_error(error):
        return http_error(error)

    @app.errorhandler(DuplicateKeyError)
    def document_exists_error(_):
        return generic_error('Document already exists.', 409)

    @app.errorhandler(422)
    def handle_unprocessable_entity(err):
        """
        shamelessly stolen from
        https://webargs.readthedocs.io/en/latest/framework_support.html#error-handling
        """
        # webargs attaches additional metadata to the `data` attribute
        exc = getattr(err, 'exc')
        if exc:
            # Get validations from the ValidationError object
            messages = exc.messages
        else:
            messages = ['Invalid request']
        return jsonify({
            'messages': messages,
        }), 422
