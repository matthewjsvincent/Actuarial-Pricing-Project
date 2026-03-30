from pathlib import Path
import sys


def app_base_dir() -> Path:
    """
    Return the base directory for the application in both:
    - normal Python execution
    - PyInstaller packaged execution
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """
    Return a writable directory for app-created files such as:
    - SQLite database
    - trained model artifacts
    - exports
    """
    base = Path.cwd() / "app_data"
    base.mkdir(exist_ok=True)
    return base


def bundled_data_dir() -> Path:
    return app_base_dir() / "data"