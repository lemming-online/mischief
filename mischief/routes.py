# -*- coding: utf-8 -*-
"""
defines the miscellaneous routes that mischief exposes
"""
from mischief import app


@app.route('/health')
def health():
    return "ヽ(´ᗜ｀)ノ"
