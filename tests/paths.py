"""Shared paths for the test suite."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT_DIR = PROJECT_ROOT / "experiment"
RESULTS_DIR = PROJECT_ROOT / "results"
COLLECTING_SOCIETY = PROJECT_ROOT / "collecting-society"
GLOSSARY_PATH = COLLECTING_SOCIETY / "GLOSSARY.yaml"
SOURCE_ROOT = COLLECTING_SOCIETY / "src"
