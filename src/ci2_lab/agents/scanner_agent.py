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
            "scripts": [],
            "documentation": [],
            "notebooks": [],
            "config": [],
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

        if lower_name == "readme.md":
            return "documentation"
        if lower_name in {"requirements.txt", "pyproject.toml"}:
            return "dependencies"
        if lower_name == "package.json":
            return "node"
        if name == "Dockerfile":
            return "docker"
        if name == "Makefile" or suffix == ".sh":
            return "scripts"
        if suffix == ".py":
            return "python"
        if suffix == ".ipynb":
            return "notebooks"
        if suffix in {".yml", ".yaml"}:
            return "config"

        return None
