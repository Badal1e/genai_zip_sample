from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return PROJECT_ROOT / "data"


def models_dir() -> Path:
    return PROJECT_ROOT / "models"


def data_path(*parts: str) -> Path:
    p = data_dir()
    return p.joinpath(*parts) if parts else p


def models_path(*parts: str) -> Path:
    p = models_dir()
    return p.joinpath(*parts) if parts else p


def logs_dir() -> Path:
    d = PROJECT_ROOT / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d
