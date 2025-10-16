from __future__ import annotations

from importlib import resources

import pytest

import os

import spaps_server_quickstart


def _template_path(*parts: str):
    template_resource = resources.files(spaps_server_quickstart) / "templates"
    for part in parts:
        template_resource = template_resource / part
    return resources.as_file(template_resource)


def _load_operations_template(path: str) -> str:
    with _template_path("operations", path) as file_path:
        return file_path.read_text()


@pytest.mark.parametrize(
    "filename",
    [
        "Makefile",
        ".env.production.example",
        "docker-compose.prod.yml",
        "deploy/deploy.sh",
    ],
)
def test_operations_templates_available(filename: str) -> None:
    content = _load_operations_template(filename)
    assert content.strip(), f"Template {filename} should not be empty"


def test_deploy_script_marked_executable() -> None:
    with _template_path("operations", "deploy", "deploy.sh") as script_path:
        assert os.access(script_path, os.X_OK), "deploy script should be executable"


@pytest.mark.parametrize(
    "filename",
    [
        ("domains", "users", "router.py"),
        ("domains", "admin", "router.py"),
    ],
)
def test_domain_templates_available(filename: tuple[str, ...]) -> None:
    with _template_path(*filename) as template_path:
        content = template_path.read_text()
        assert "require_roles" in content


def test_docker_compose_contains_placeholder_image() -> None:
    contents = _load_operations_template("docker-compose.prod.yml")
    assert "${SPAPS_IMAGE" in contents
