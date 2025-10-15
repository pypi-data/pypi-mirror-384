from __future__ import annotations

import json
import logging
import sys
from contextlib import suppress
from dataclasses import asdict, dataclass
from typing import Final

from .telemetry import SCHEMA_VERSION

_LOGGER = logging.getLogger("x_make")
_UTILITIES: Final[tuple[str, ...]] = (
    "telemetry",
    "json_board",
    "x_env_x",
    "x_http_client_x",
    "x_logging_utils_x",
    "x_subprocess_utils_x",
)


def _emit_stdout(message: str) -> bool:
    try:
        print(message)
    except (OSError, RuntimeError):
        return False
    return True


def _emit_stderr(message: str) -> bool:
    try:
        print(message, file=sys.stderr)
    except (OSError, RuntimeError):
        return False
    return True


def _info(*parts: object) -> None:
    msg = " ".join(str(part) for part in parts)
    with suppress(Exception):
        _LOGGER.info("%s", msg)
    if not _emit_stdout(msg):
        with suppress(Exception):
            sys.stdout.write(msg + "\n")


def _error(*parts: object) -> None:
    msg = " ".join(str(part) for part in parts)
    with suppress(Exception):
        _LOGGER.error("%s", msg)
    if not _emit_stderr(msg):
        with suppress(Exception):
            sys.stderr.write(msg + "\n")


@dataclass(slots=True)
class CommonDiagnostics:
    telemetry_schema_version: str
    utilities: tuple[str, ...]
    ctx_present: bool


class XClsMakeCommonX:
    """Lightweight diagnostics provider for the shared helpers package."""

    def __init__(self, ctx: object | None = None) -> None:
        self._ctx = ctx

    def diagnostics(self) -> CommonDiagnostics:
        return CommonDiagnostics(
            telemetry_schema_version=SCHEMA_VERSION,
            utilities=_UTILITIES,
            ctx_present=self._ctx is not None,
        )

    def run(self) -> CommonDiagnostics:
        diagnostics = self.diagnostics()
        _info(
            "x_make_common_x ready",
            f"telemetry_schema={diagnostics.telemetry_schema_version}",
            f"utilities={', '.join(diagnostics.utilities)}",
            f"ctx={'present' if diagnostics.ctx_present else 'absent'}",
        )
        return diagnostics


def main() -> CommonDiagnostics:
    return XClsMakeCommonX().run()


if __name__ == "__main__":
    try:
        diagnostics = main()
        payload = json.dumps(asdict(diagnostics), indent=2)
        _info(payload)
    except Exception as exc:  # noqa: BLE001 - surface failure for operators
        _error("x_make_common_x diagnostics failed:", exc)
        raise SystemExit(1)


x_cls_make_common_x = XClsMakeCommonX
