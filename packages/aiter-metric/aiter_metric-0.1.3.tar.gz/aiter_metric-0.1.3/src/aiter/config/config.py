import os
from pathlib import Path
import yaml

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def get_api_key(api) -> str | None:
    return os.getenv("MISTRAL_API_KEY") if api == "mistral" else os.getenv("GOOGLE_API_KEY") if api == "gemini" else None

def require_api_key(api) -> str:
    key = get_api_key(api)
    if not key:
        raise RuntimeError(
            "Missing API_KEY. "
            "Set it as an environment variable or pass it explicitly to the Scorer(api_key=...) constructor."
        )
    return key


def _read_yaml_safe(package: str, rel_in_pkg: str, rel_in_repo: str):
    """
    Essaie d'abord de lire un fichier YAML embarqué dans le package (installé),
    sinon retombe sur le chemin source du repo (dev local sans install).
    """
    try:
        from importlib.resources import files
        path = files(package) / rel_in_pkg
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / rel_in_repo
        return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_models_config():
    return _read_yaml_safe(
        package="aiter.config",
        rel_in_pkg="models.yaml",
        rel_in_repo="src/aiter/config/models.yaml",
    )


def load_versions_config():
    return _read_yaml_safe(
        package="aiter.config",
        rel_in_pkg="versions.yaml",
        rel_in_repo="src/aiter/config/versions.yaml",
    )


def get_prompts_dir():
    try:
        from importlib.resources import files
        return files("aiter") / "prompts"
    except Exception:
        repo_root = Path(__file__).resolve().parents[3]
        return repo_root / "src" / "aiter" / "prompts"

MODELS_CONFIG = load_models_config()
PROMPTS = load_versions_config()
PROMPTS_DIR = get_prompts_dir()
