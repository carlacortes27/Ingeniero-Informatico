from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse


class GitHubCloneError(RuntimeError):
    pass


def is_github_url(input_value: str) -> bool:
    parsed = urlparse(input_value)
    return parsed.scheme == "https" and parsed.netloc.lower() == "github.com"


def _repo_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]

    if len(parts) != 2:
        raise GitHubCloneError("La URL no es un repositorio de GitHub valido.")

    repo_name = parts[1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    if not repo_name:
        raise GitHubCloneError("La URL no es un repositorio de GitHub valido.")

    return repo_name


def clone_github_repo(url: str) -> tuple[str, str]:
    if not is_github_url(url):
        raise GitHubCloneError("La URL no es un repositorio de GitHub valido.")

    repo_name = _repo_name_from_url(url)
    temporary_root = tempfile.mkdtemp(prefix="ci2-lab-")
    destination = Path(temporary_root) / repo_name

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(destination)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        remove_temporary_directory(temporary_root)
        raise GitHubCloneError("Git no esta instalado en el sistema.") from error
    except subprocess.CalledProcessError as error:
        remove_temporary_directory(temporary_root)
        details = (error.stderr or error.stdout or "").strip()
        message = "La clonacion del repositorio ha fallado."
        if details:
            message = f"{message} {details}"
        raise GitHubCloneError(message) from error

    return str(destination), repo_name


def remove_temporary_directory(path: str | Path | None) -> None:
    if path is None:
        return

    target = Path(path)
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
