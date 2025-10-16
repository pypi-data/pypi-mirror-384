"""Pytest configuration for amsdal_workflow tests."""

import os
from collections.abc import Generator
from unittest import mock

import pytest
from amsdal.manager import AmsdalManager
from amsdal_data.test_utils.config import sqlite_config
from amsdal_utils.config.manager import AmsdalConfigManager


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        '--internal',
        action='store_true',
        default=False,
        help='Use internal LangGraph SqliteSaver instead of AmsdalCheckpointSaver',
    )


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with proper configuration."""
    # Set environment variables to disable cloud features
    os.environ['AMSDAL_DISABLE_CLOUD'] = 'true'
    os.environ['AMSDAL_DISABLE_AUTH'] = 'true'

    # Mock authentication methods to prevent prompts
    with mock.patch('amsdal.cloud.services.auth.signup_service.want_signup_input', return_value=False):
        with mock.patch('amsdal.manager.AmsdalManager.authenticate', return_value=None):
            with mock.patch('amsdal.manager.AsyncAmsdalManager.authenticate', return_value=None):
                yield


@pytest.fixture
def amsdal_config():
    """Set up AMSDAL configuration for tests."""
    with sqlite_config() as config:
        AmsdalConfigManager().set_config(config)
        try:
            yield config
        finally:
            AmsdalConfigManager.invalidate()


@pytest.fixture
def amsdal_manager(amsdal_config) -> Generator[AmsdalManager, None, None]:
    """Set up AMSDAL manager for tests."""
    manager = AmsdalManager()
    manager.setup()
    try:
        yield manager
    finally:
        manager.teardown()
        AmsdalManager.invalidate()
