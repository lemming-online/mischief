# -*- coding: utf-8 -*-
"""
defines a wrapper for the mailgun API
"""
import requests


class Mail:
    """flask friendly mailgun API wrapper."""
    def __init__(self, app):
        self.api = app.config['MAILGUN_URI']
        self.api_key = app.config['MAILGUN_API_KEY']
        self.domain = app.config['MAILGUN_DOMAIN']
        self.app_email = 'Team Lemming <team@{}>'.format(self.domain)

    def route(self, name):
        """convert a route name into a full URL"""
        return '{}/{}'.format(self.api, name)

    def send(self, message, recipient, sender=None, subject='Message from Team Lemming'):
        """sends an email"""
        requests.post(
            self.route('messages'),
            auth=('api', self.api_key),
            data={
                'from': sender or self.app_email,
                'to': recipient,
                'subject': subject,
                'html': message,
            }
        )
