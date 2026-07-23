"""Validation tests for the helper-family disposition matrix."""

from __future__ import annotations

from pathlib import Path

import pytest


ALLOWED_DISPOSITIONS = {
    "migrate",
    "seed",
    "re-learn",
    "replace with room default",
    "replace with person plus room default",
    "retire",
}

EXPECTED_FAMILY_IDS = {
    "HSF-01",
    "HSF-02",
    "HSF-03",
    "HSF-04",
    "HSF-05",
    "HSF-06",
}


@pytest.fixture
def enable_custom_integrations() -> None:
    """Satisfy the shared test conftest autouse dependency for this standalone audit test."""
    return None


def _matrix_text() -> str:
    return (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "governance"
        / "experience-continuity"
        / "experience-continuity-helper-family-disposition-matrix.md"
    ).read_text(encoding="utf-8")


def test_helper_family_disposition_matrix_lists_all_expected_families() -> None:
    """The matrix should enumerate every in-scope helper family once."""
    matrix_text = _matrix_text()

    for family_id in EXPECTED_FAMILY_IDS:
        assert family_id in matrix_text

    row_ids = []
    for line in matrix_text.splitlines():
        if not line.startswith("| HSF-"):
            continue
        row_ids.append(line.split("|")[1].strip())

    assert set(row_ids) == EXPECTED_FAMILY_IDS


def test_helper_family_disposition_matrix_uses_only_approved_dispositions() -> None:
    """Every matrix row should use one of the governed disposition values."""
    matrix_text = _matrix_text()

    for line in matrix_text.splitlines():
        if not line.startswith("| HSF-"):
            continue
        columns = [column.strip() for column in line.split("|") if column.strip()]
        disposition = columns[3]
        assert disposition in ALLOWED_DISPOSITIONS
