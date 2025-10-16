from __future__ import annotations

from pathlib import Path

import pytest

from spaps_server_quickstart.alembic.naming import (
    MigrationNamingError,
    build_revision_message,
    collect_directory_errors,
    ensure_known_domain,
    slugify_title,
    validate_migration_filename,
)


def test_slugify_title_and_revision_message() -> None:
    assert slugify_title("Add Practitioner Table!") == "add_practitioner_table"
    message = build_revision_message("infra", "Add Practitioner Table")
    assert message == "infra add practitioner table"


def test_validate_migration_filename_success(tmp_path: Path) -> None:
    file_path = tmp_path / "202501010000_practitioner_create_table.py"
    file_path.write_text("")

    validate_migration_filename(file_path, allowed_domains=("infra", "practitioner"))


def test_validate_migration_filename_failure(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad_migration.py"
    bad_file.write_text("")

    with pytest.raises(MigrationNamingError):
        validate_migration_filename(bad_file)


def test_collect_directory_errors(tmp_path: Path) -> None:
    valid = tmp_path / "202501010000_infra_create_table.py"
    valid.write_text("")
    invalid = tmp_path / "202501020000_unknown_create_table.py"
    invalid.write_text("")

    errors = collect_directory_errors(tmp_path, allowed_domains=("infra",))
    assert len(errors) == 1
    assert "Unknown migration domain" in errors[0]


def test_ensure_known_domain() -> None:
    assert ensure_known_domain("infra", allowed_domains=("infra",)) == "infra"
    with pytest.raises(ValueError):
        ensure_known_domain("unknown", allowed_domains=("infra",))
