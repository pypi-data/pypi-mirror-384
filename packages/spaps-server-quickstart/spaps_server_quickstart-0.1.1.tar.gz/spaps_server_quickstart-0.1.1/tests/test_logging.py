from __future__ import annotations

import logging

from spaps_server_quickstart.logging import configure_logging


class DummySettings:
    log_level = "debug"
    log_format = "console"
    log_include_tracebacks = True
    log_file_path = None
    env = "dev"


def test_configure_logging_sets_up_structlog(monkeypatch) -> None:
    basic_config_calls: dict[str, object] = {}
    structlog_calls: dict[str, object] = {}

    def fake_basicConfig(**kwargs):
        basic_config_calls.update(kwargs)

    def fake_configure(**kwargs):
        structlog_calls.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)

    import structlog

    monkeypatch.setattr(structlog, "configure", fake_configure)

    configure_logging(DummySettings())

    assert basic_config_calls["level"] == logging.DEBUG
    assert isinstance(basic_config_calls["handlers"], list)
    processors = structlog_calls["processors"]  # type: ignore[index]
    assert isinstance(processors, list)
    assert processors, "processors list should not be empty"
    assert structlog_calls["cache_logger_on_first_use"] is True
