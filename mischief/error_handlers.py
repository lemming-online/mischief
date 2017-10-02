# -*- coding: utf-8 -*-
"""
error code handlers
"""
from flask import jsonify

from mischief import app


def generic_error(error):
    return jsonify({'error': {'reason': error.description}})


@app.errorhandler(404)
def not_found(error):
    return generic_error(error)


@app.errorhandler(400)
def bad_request(error):
    return generic_error(error)


@app.errorhandler(500)
def server_error(error):
    return generic_error(error)
