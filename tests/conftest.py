# -*- coding: utf-8 -*-
"""
conftest
"""
from mischief import create_app

@pytest.fixture
def app():
    app = create_app()
    return app