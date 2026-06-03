from pathlib import Path

from ci2_lab.models import ScanResult


class ScannerAgent:
    ignored_directories = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".cache",
        ".ipynb_checkpoints",
        ".idea",
        ".vscode",
    }

    def scan(self, project_path: str | Path) -> ScanResult:
        root = Path(project_path).resolve()
        files: dict[str, list[str]] = {
            "python": [],
            "dependencies": [],
            "node": [],
            "docker": [],
            "ci": [],
            "scripts": [],
            "documentation": [],
            "notebooks": [],
            "config": [],
            "locks": [],
        }

        for path in self._walk(root):
            category = self._classify(path)
            if category is None:
                continue

            relative_path = path.relative_to(root).as_posix()
            files[category].append(relative_path)

        sorted_files = {
            category: sorted(set(paths))
            for category, paths in files.items()
            if paths
        }

        return ScanResult(
            project_name=root.name,
            project_path=str(root),
            files=sorted_files,
        )

    def _walk(self, root: Path) -> list[Path]:
        paths: list[Path] = []

        for path in root.rglob("*"):
            if any(part in self.ignored_directories for part in path.parts):
                continue
            if path.is_file():
                paths.append(path)

        return sorted(paths)

    def _classify(self, path: Path) -> str | None:
        name = path.name
        lower_name = name.lower()
        suffix = path.suffix.lower()
        relative_parts = tuple(part.lower() for part in path.parts)

        if lower_name in {
            "readme.md",
            "readme.rst",
            "install.md",
            "contributing.md",
            "changelog.md",
        }:
            return "documentation"
        if "docs" in relative_parts:
            return "documentation"
        if lower_name in {
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "environment.yml",
            "environment.yaml",
            "pipfile",
        }:
            return "dependencies"
        if lower_name in {
            "poetry.lock",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        }:
            return "locks"
        if lower_name == "package.json":
            return "node"
        if name == "Dockerfile" or lower_name in {"docker-compose.yml", "docker-compose.yaml"}:
            return "docker"
        if name == "Makefile" or suffix == ".sh":
            return "scripts"
        if lower_name == ".gitlab-ci.yml":
            return "ci"
        if ".github" in relative_parts and "workflows" in relative_parts:
            return "ci"
        if suffix == ".py":
            return "python"
        if suffix == ".ipynb":
            return "notebooks"
        if suffix in {".yml", ".yaml"}:
            return "config"

        return None
