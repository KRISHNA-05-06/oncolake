"""Smoke tests for the OncoLake Python surface.

These import the two runnable modules in the repo and assert contracts that
would actually break the pipeline if violated: the S3 landing-file naming rule
the Lambda enforces, and the extraction prompt matching the columns the loader
writes into STAGING.CORTEX_EXTRACTIONS.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# validate_and_alert builds boto3 clients at import time, which needs a region
# but no credentials. Set one before the module is loaded.
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def _load(name, relative_path):
    """Import a module by file path.

    Needed because neither location is an importable package: `aws/lambda/` uses
    a Python keyword as a directory name, and `src/` has no __init__.py.
    """
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validate_and_alert = _load("validate_and_alert", "aws/lambda/validate_and_alert.py")
extract_to_snowflake = _load("extract_to_snowflake", "src/extract_to_snowflake.py")

# Columns main() populates from the model's JSON response.
EXTRACTED_FIELDS = ("primary_site", "ajcc_stage", "tnm_stage", "treatments", "biomarkers")


def test_sample_lab_file_passes_lambda_naming_rule():
    """The checked-in sample file must satisfy the rule the Lambda enforces.

    If these drift apart, the Lambda alerts on the repo's own sample data.
    """
    sample = REPO_ROOT / "data/sample/lab_results_20260719_a1.csv"
    assert sample.exists(), "sample lab file is missing from data/sample/"
    assert validate_and_alert.FILENAME_RE.match(sample.name)


@pytest.mark.parametrize(
    "filename",
    [
        "lab_results_2026071_a1.csv",  # 7-digit date
        "lab_results_20260719_A1.csv",  # uppercase id
        "lab_results_20260719_a1.txt",  # wrong extension
        "notes_deidentified.csv",  # wrong prefix
    ],
)
def test_lambda_rejects_malformed_filenames(filename):
    assert validate_and_alert.FILENAME_RE.match(filename) is None


def test_lambda_handler_accepts_a_wellformed_s3_event():
    event = {"Records": [{"s3": {"object": {"key": "lab_results/lab_results_20260719_a1.csv"}}}]}
    assert validate_and_alert.handler(event, None) == {"statusCode": 200, "body": "validated"}


def test_prompt_requests_every_field_the_loader_stores():
    """Every column the INSERT fills must be a key the prompt asks the model for."""
    for field in EXTRACTED_FIELDS:
        assert field in extract_to_snowflake.PROMPT, f"prompt never asks for {field}"


def test_prompt_interpolates_the_note():
    rendered = extract_to_snowflake.PROMPT.format(note="Patient with stage IIIA lung adenocarcinoma.")
    assert "stage IIIA lung adenocarcinoma" in rendered
    assert "{note}" not in rendered
