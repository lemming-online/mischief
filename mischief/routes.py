# -*- coding: utf-8 -*-
"""
defines the miscellaneous routes that mischief exposes
"""
from flask import url_for

from mischief import app


@app.route('/health')
def health():
    return "ヽ(´ᗜ｀)ノ"


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


# Both shamelessly stolen from https://stackoverflow.com/questions/13317536/get-a-list-of-all-routes-defined-in-the-app
@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    return links
