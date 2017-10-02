# -*- coding: utf-8 -*-
"""
internal flask extension for RESTfulness
"""
from flask import Flask, Response, jsonify, request, abort


# shameless stolen from https://blog.miguelgrinberg.com/post/customizing-the-flask-response-class
class JSONResponse(Response):
    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, (dict, list)):
            rv = jsonify(rv)
        return super().force_type(rv, environ)


class RatNap(Flask):
    response_class = JSONResponse

    # shamelessly stolen from flask tutorials here: http://flask.pocoo.org/docs/0.12/views/
    # modified to support /resource/item vs. /resource
    def register_api(self, view, endpoint, url, pk, pk_type):
        view_func = view.as_view(endpoint)
        if pk:
            self.add_url_rule(
                '%s/<%s:%s>' % (url, pk_type, pk),
                view_func=view_func,
                methods=['GET', 'PUT', 'DELETE'],
            )
        else:
            self.add_url_rule(
                url,
                view_func=view_func,
                methods=['GET', 'POST'],
            )

    def resource(self, endpoint, url, pk=None, pk_type='ObjectId'):
        app = self

        class ResourceWrapper:
            def __init__(self, resource_cls):
                self.resource = resource_cls
                app.register_api(resource_cls, endpoint, url, pk, pk_type)

            def __call__(self):
                return self.resource()
        return ResourceWrapper

    def use_schema(self, schema_cls, load=False, dump=True, many=False):
        class SchemaWrapper:
            def __init__(self, resource_fn):
                self.fn = resource_fn

            def __call__(self, *args, **kwargs):
                if load:
                    raw_params = request.get_json()
                    result = schema_cls.load(raw_params, many=many)
                    if result.errors:
                        print('errors', result.errors)
                        # TODO: pls god use python logging
                        abort(400)
                    kwargs = {**kwargs, 'data': result.data}
                res = self.fn(self, *args, **kwargs)
                if dump:
                    res = schema_cls.dump(res, many=many)
                return res
        return SchemaWrapper
