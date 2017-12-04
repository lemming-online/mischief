# -*- coding: utf-8 -*-
"""
mischief
========

mischief is the primary backend component of the
help room management and ticketing platform
'lemming.online'
"""
from flask import Flask
from flask_socketio import SocketIO

from mischief.util import initialize

socketio = SocketIO()

def create_app(config=None):
    """
    creates a mischief app instance with an optional
    config class that will be overridden by shell settings

    :param config: optional config class
    :return: mischief instance
    """
    _app = Flask('mischief')
    _app.config.from_object('mischief.config.Default')
    _app.config.from_object(config or {})
    _app.config.from_envvar('MISCHIEF_CONFIG', silent=True)

    initialize(_app)
    socketio.init_app(_app)

    @socketio.on('join')
    def on_join(data):
        room = data['group_id']
        join_room(room)
        send('Successfully joined room: ' + room)

    @socketio.on('leave')
    def on_leave(data):
        room = data['group_id']
        leave_room(room)
        send('Successfully left room: ' + room)

    return _app
