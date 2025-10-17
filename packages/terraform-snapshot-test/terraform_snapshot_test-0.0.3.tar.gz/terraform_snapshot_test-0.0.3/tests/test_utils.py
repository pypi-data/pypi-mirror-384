import pytest

from src.terraform_snapshot_test import (
    assert_expectations,
    get_json_from_file,
)


def test_assertions_synthetis_ok():
    assert_expectations(
        snapshot=get_json_from_file("tests/__snapshots__/test_terraform_snapshot/test_synthesizes_properly.json"),
        snapshot_type="synthesis",
        folder_path="tests/expectations_ok",
    )


def test_assertions_planned_values_ok():
    assert_expectations(
        snapshot=get_json_from_file("tests/__snapshots__/test_terraform_snapshot/test_planned_values.json"),
        snapshot_type="planned_values",
        folder_path="tests/expectations_ok",
    )


def test_assertions_synthetis_nok():
    caught_exception = False
    try:
        assert_expectations(
            snapshot=get_json_from_file("tests/__snapshots__/test_terraform_snapshot/test_synthesizes_properly.json"),
            snapshot_type="synthesis",
            folder_path="tests/expectations_nok",
        )
    except AssertionError:
        caught_exception = True
    if not caught_exception:
        pytest.fail("AssertionError expected but not raised")


def test_assertions_planned_values_nok():
    caught_exception = False
    try:
        assert_expectations(
            snapshot=get_json_from_file("tests/__snapshots__/test_terraform_snapshot/test_planned_values.json"),
            snapshot_type="planned_values",
            folder_path="tests/expectations_nok",
        )
    except AssertionError:
        caught_exception = True
    if not caught_exception:
        pytest.fail("AssertionError expected but not raised")
