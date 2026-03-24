"""Shared fixtures for the semantic erosion test suite."""
import sys

import pytest
import yaml

from tests.paths import EXPERIMENT_DIR, GLOSSARY_PATH, SOURCE_ROOT

# Add experiment/ to sys.path so we can import modules
sys.path.insert(0, str(EXPERIMENT_DIR))


@pytest.fixture
def glossary_path():
    return str(GLOSSARY_PATH)


@pytest.fixture
def glossary_terms():
    with open(GLOSSARY_PATH) as f:
        data = yaml.safe_load(f)
    return data["terms"]


@pytest.fixture
def source_root():
    return str(SOURCE_ROOT)


@pytest.fixture
def sample_by_category():
    """A minimal by_category dict simulating extracted identifiers."""
    return {
        "class_name": {"RightsHolder", "MusicalWork", "DistributionRun"},
        "interface_name": set(),
        "enum_name": {"ExploitationType"},
        "record_name": set(),
        "method_name": {"calculateRoyalties", "resolveRightsShares"},
        "field_name": {"rightsHolderId", "musicalWorkId"},
        "parameter_name": {"periodStart", "periodEnd"},
        "local_variable": {"statement"},
    }
