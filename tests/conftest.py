# -*- coding: utf-8 -*-
"""
conftest
"""
import pytest

from mischief import create_app


@pytest.fixture
def app():
    return create_app()
