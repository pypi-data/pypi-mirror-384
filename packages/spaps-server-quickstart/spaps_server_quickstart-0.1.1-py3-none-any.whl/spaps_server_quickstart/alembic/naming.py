"""
Migration filename validation helpers.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ALLOWED_DOMAINS: tuple[str, ...] = ("infra",)

FILENAME_PATTERN = re.compile(
    r"^(?P<revision>[0-9a-z]{12})_(?P<domain>[a-z0-9]+)_(?P<slug>[a-z0-9_]+)\.py$"
)


class MigrationNamingError(ValueError):
    """Raised when a migration filename violates naming conventions."""


@dataclass(slots=True, frozen=True)
class MigrationName:
    revision: str
    domain: str
    slug: str


def slugify_title(title: str) -> str:
    """Normalize arbitrary text to a filesystem-safe slug."""
    lowered = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "migration"


def build_revision_message(domain: str, title: str, *, allowed_domains: Sequence[str] | None = None) -> str:
    """Compose the Alembic revision message used for naming files."""
    normalized_domain = _normalize_domain(domain, allowed_domains)
    normalized_title = " ".join(title.lower().split())
    if not normalized_title:
        normalized_title = "migration"
    return f"{normalized_domain} {normalized_title}"


def validate_migration_filename(
    path: Path,
    *,
    allowed_domains: Sequence[str] | None = None,
) -> None:
    """Validate a migration filename, raising if it does not conform."""
    domains = tuple(allowed_domains or DEFAULT_ALLOWED_DOMAINS)
    name = path.name
    match = FILENAME_PATTERN.match(name)
    if not match:
        revision_candidate = name.split("_", 1)[0]
        if not revision_candidate.isdigit() or len(revision_candidate) != 12:
            raise MigrationNamingError(
                f"{name!r}: Revision id must be a 12-digit timestamp."
            )
        raise MigrationNamingError(
            f"{name!r} should follow '<revision>_<domain>_<slug>.py' format "
            "with a 12-digit timestamp revision id."
        )
    parsed = MigrationName(
        revision=match.group("revision"),
        domain=match.group("domain"),
        slug=match.group("slug"),
    )

    _validate_revision_id(parsed.revision, name)
    _validate_domain(parsed.domain, name, domains)
    _validate_slug(parsed.slug, name)


def collect_directory_errors(
    directory: Path,
    *,
    allowed_domains: Sequence[str] | None = None,
) -> list[str]:
    """Return validation error strings for each invalid migration file."""
    errors: list[str] = []
    for path in sorted(_iter_migration_files(directory)):
        try:
            validate_migration_filename(path, allowed_domains=allowed_domains)
        except MigrationNamingError as exc:
            errors.append(f"{path.name}: {exc}")
    return errors


def ensure_known_domain(domain: str, *, allowed_domains: Sequence[str] | None = None) -> str:
    """Return a normalized domain or raise ValueError if unsupported."""
    return _normalize_domain(domain, allowed_domains)


def allowed_domains(domains: Sequence[str] | None = None) -> Sequence[str]:
    """Expose allowed migration domains for external tooling."""
    return tuple(domains or DEFAULT_ALLOWED_DOMAINS)


def _validate_revision_id(revision: str, filename: str) -> None:
    if len(revision) != 12 or not revision.isdigit():
        raise MigrationNamingError(
            f"{filename!r}: Revision id must be a 12-digit timestamp."
        )


def _validate_domain(domain: str, filename: str, allowed: Sequence[str]) -> None:
    if domain not in allowed:
        allowed_str = ", ".join(allowed)
        raise MigrationNamingError(
            f"{filename!r}: Unknown migration domain '{domain}'. "
            f"Filenames should include a domain prefix from: {allowed_str}."
        )


def _validate_slug(slug: str, filename: str) -> None:
    if not slug or slug == "_":
        raise MigrationNamingError(
            f"{filename!r}: Slug segment must describe the migration."
        )


def _normalize_domain(domain: str, allowed_domains: Sequence[str] | None = None) -> str:
    domains = tuple(allowed_domains or DEFAULT_ALLOWED_DOMAINS)
    normalized = domain.strip().lower().replace("-", "_")
    if normalized not in domains:
        allowed_str = ", ".join(domains)
        raise ValueError(
            f"Unknown migration domain '{domain}'. Allowed domains: {allowed_str}."
        )
    return normalized


def _iter_migration_files(directory: Path) -> Iterable[Path]:
    return directory.glob("*.py")
