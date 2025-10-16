#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test configuration for RegScale integrations."""
import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "stress: mark test as a stress test (requires --stress flag to run)")


def pytest_addoption(parser):
    """Add command line options to pytest."""
    parser.addoption(
        "--stress",
        action="store_true",
        default=False,
        help="Run stress tests (tests that generate and process large amounts of data)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip stress tests unless --stress option is specified."""
    if not config.getoption("--stress"):
        skip_stress = pytest.mark.skip(reason="Need --stress option to run")
        for item in items:
            if "stress" in item.keywords:
                item.add_marker(skip_stress)
