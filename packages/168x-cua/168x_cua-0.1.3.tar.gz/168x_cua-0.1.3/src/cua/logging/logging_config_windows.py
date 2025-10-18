"""
Logging configuration for the CUA client on Windows.

*   **Daily rotating file handler** – logs are saved to C:\Logs with daily rotation
*   **Maximum 10 backup files** – keeps the last 10 days of logs
*   **No console handler** – can run via pythonw.exe without spawning a console window
*   Un‑caught exceptions are routed into the log file via ``sys.excepthook``
*   **Console hiding** – If any library creates a console window after pythonw.exe
    starts, we immediately hide it using Windows API
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Final
from logging.handlers import TimedRotatingFileHandler
import ctypes
import platform

_LOG_DIR: Final = Path(r"C:\168x-cua\logs")
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE: Final = _LOG_DIR / "cua.log"

# ---------------------------------------------------------------------------
#  CRITICAL: Hide console window if one appears
#  This simple solution handles cases where libraries like pyautogui create
#  a console window even when running under pythonw.exe
# ---------------------------------------------------------------------------
if platform.system() == "Windows":
    try:
        GetConsoleWindow = ctypes.windll.kernel32.GetConsoleWindow  # type: ignore[attr-defined]
        ShowWindow = ctypes.windll.user32.ShowWindow  # type: ignore[attr-defined]
        SW_HIDE = 0
        hwnd = GetConsoleWindow()
        if hwnd:
            ShowWindow(hwnd, SW_HIDE)
    except Exception:
        # Best-effort; ignore if anything goes wrong (e.g. DLL missing)
        pass

# ---------------------------------------------------------------------------
#  Formatter – plain, timestamped lines suitable for tail & parsing
# ---------------------------------------------------------------------------
_plain_fmt = logging.Formatter(
    fmt="[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def setup_logging(level: str = "DEBUG") -> None:  # noqa: D401 (imperative mood)
    """Configure global logging with daily rotation (file‑only; no console handler).

    Parameters
    ----------
    level : str, default "DEBUG"
        The minimum level for the *cua* logger family. Third‑party
        loggers stay at WARNING to avoid noise.
    
    Notes
    -----
    - Logs are saved to C:\\Logs\\cua.log
    - Files rotate daily at midnight
    - Maximum 10 backup files are kept (10 days of history)
    - Backup files are named cua.log.YYYY-MM-DD
    """

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.WARNING)  # suppress most third‑party chatter
    root.handlers.clear()

    # --- Timed Rotating File handler ----------------------------------------
    # when='midnight': rotate at midnight
    # interval=1: rotate every day
    # backupCount=10: keep 10 backup files
    file_handler = TimedRotatingFileHandler(
        _LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_plain_fmt)
    # Set suffix for backup files (YYYY-MM-DD format)
    file_handler.suffix = "%Y-%m-%d"
    root.addHandler(file_handler)

    # --- cua.* logger (more verbose) ----------------------------------------
    client_logger = logging.getLogger("cua")
    client_logger.setLevel(numeric_level)
    client_logger.propagate = True  # still goes through root -> file handler

    # --- tame noisy libraries -----------------------------------------------
    for noisy in (
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "httpx",
        "httpcore",
    ):
        lg = logging.getLogger(noisy)
        lg.setLevel(logging.WARNING)
        lg.propagate = True

    client_logger.info(
        "Logging configured – log directory: %s – level: %s – rotation: daily – backups: 10",
        _LOG_DIR,
        level.upper(),
    )
    client_logger.debug("Debug logging enabled for cua components")

    # --- capture uncaught exceptions ----------------------------------------
    def _log_excepthook(exc_type, exc_value, tb):  # type: ignore[pep8-naming]
        client_logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, tb))

    sys.excepthook = _log_excepthook

