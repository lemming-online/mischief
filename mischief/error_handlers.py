# -*- coding: utf-8 -*-
"""
error code handlers
"""
from mischief import app


@app.errorhandler(404)
def not_found(error):
    return {}