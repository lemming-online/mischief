# -*- coding: utf-8 -*-
"""
decorator functions
"""
from webargs.flaskparser import use_args

def use_args_with(schema_cls, schema_kwargs=None, **kwargs):
    """
    shamelessly stolen from
    https://webargs.readthedocs.io/en/latest/advanced.html#schema-factories
    """
    schema_kwargs = schema_kwargs or {}
    def factory(request):
        # Filter based on 'fields' query parameter
        only = request.args.get('fields', None)
        # Respect partial updates for PATCH requests
        partial = request.method == 'PATCH'
        # Add current request to the schema's context
        # and ensure we're always using strict mode
        return schema_cls(
            only=only, partial=partial, strict=True,
            context={'request': request}, **schema_kwargs
        )
    return use_args(factory, **kwargs)
