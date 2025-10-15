from __future__ import annotations

import sys
import warnings
from pathlib import Path
from unittest import mock

import pytest

try:  # pragma: no cover - best effort import guard
    import pytest_cov  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover - executed when plugin is missing
    _HAS_PYTEST_COV = False
else:  # pragma: no cover - executed in local dev envs with pytest-cov
    _HAS_PYTEST_COV = True


_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if _SRC_PATH.exists() and str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))


class _PatchProxy:
    def __init__(self, register_patch):
        self._register_patch = register_patch

    def __call__(self, *args, **kwargs):
        patcher = mock.patch(*args, **kwargs)
        return self._register_patch(patcher)

    def object(self, *args, **kwargs):
        patcher = mock.patch.object(*args, **kwargs)
        return self._register_patch(patcher)


class _SimpleMocker:
    """Lightweight replacement for :mod:`pytest-mock`'s ``mocker`` fixture."""

    Mock = staticmethod(mock.Mock)
    MagicMock = staticmethod(mock.MagicMock)
    call = mock.call
    ANY = mock.ANY
    sentinel = mock.sentinel

    def __init__(self) -> None:
        self._patches: list[object] = []
        self.patch = _PatchProxy(self._register)

    def _register(self, patcher):
        self._patches.append(patcher)
        return patcher.start()

    def stopall(self) -> None:
        while self._patches:
            self._patches.pop().stop()

    def spy(self, obj, attribute: str):
        """Partially emulate :meth:`pytest_mock.plugin.MockerFixture.spy`.

        The helper mirrors the behaviour of the original fixture closely
        enough for the project's test-suite by delegating to
        :func:`unittest.mock.patch.object` with ``wraps``.
        """

        target = getattr(obj, attribute)
        patcher = mock.patch.object(obj, attribute, wraps=target)
        return self._register(patcher)


@pytest.fixture
def mocker():
    helper = _SimpleMocker()
    try:
        yield helper
    finally:
        helper.stopall()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register stub coverage options when pytest-cov is unavailable.

    The options mimic the interface provided by ``pytest-cov`` so that
    existing ``pytest.ini`` configuration and command line usage keep working
    even though no coverage report is produced in environments without the
    plugin.
    """

    if _HAS_PYTEST_COV:
        return

    group = parser.getgroup("coverage")
    group.addoption(
        "--cov",
        action="append",
        dest="cov",
        default=[],
        metavar="MODULE",
        help="Stub option registered when pytest-cov is not installed.",
    )
    group.addoption(
        "--cov-report",
        action="append",
        dest="cov_report",
        default=[],
        metavar="TYPE",
        help="Stub option registered when pytest-cov is not installed.",
    )
    group.addoption(
        "--cov-fail-under",
        action="store",
        dest="cov_fail_under",
        default=None,
        metavar="MIN",
        type=float,
        help="Stub option registered when pytest-cov is not installed.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Inform the user that coverage options are being ignored."""

    if _HAS_PYTEST_COV:
        return

    cov_options = bool(config.option.cov or config.option.cov_report)
    fail_under_set = config.option.cov_fail_under is not None

    if cov_options or fail_under_set:
        warnings.warn(
            "pytest-cov is not installed; coverage related options are ignored.",
            RuntimeWarning,
            stacklevel=2,
        )


def pytest_report_header(config: pytest.Config) -> str | None:
    """Display a short note in the Pytest header when coverage is stubbed."""

    if _HAS_PYTEST_COV:
        return None

    if config.option.cov or config.option.cov_report or config.option.cov_fail_under is not None:
        return "coverage plugin not available - stub options active"
    return None