# -*- coding: utf-8 -*-
"""
mailgun wrapper
"""
import requests


class MailGunner:
    key = None
    api = None

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.key = app.config['MAILGUN_API_KEY']
        self.api = 'https://api.mailgun.net/v3/{}/messages'.format(app.config['MAILGUN_DOMAIN'])

    def send(self, to, content, sender='Team Lemming <team@lemming.online>', subject='Message from Team Lemming'):
        return requests.post(
            self.api,
            auth=('api', self.key),
            data={'from': sender,
                  'to': to,
                  'subject': subject,
                  'html': content})
