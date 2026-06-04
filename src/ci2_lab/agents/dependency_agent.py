import json
from pathlib import Path
import re
import tomllib

from ci2_lab.models import ScanResult


class DependencyAgent:
    def analyze(self, project_path: str | Path, scan_result: ScanResult) -> dict:
        root = Path(project_path).resolve()
        files = scan_result.files

        python_dependencies: list[str] = []
        node_dependencies: list[str] = []
        node_dev_dependencies: list[str] = []
        package_managers: list[str] = []

        requirements_path = self._find_file(
            root,
            files.get("dependencies", []),
            "requirements.txt",
        )
        if requirements_path:
            package_managers.append("pip")
            python_dependencies = self._read_requirements(requirements_path)

        if self._has_file(files.get("dependencies", []), "pyproject.toml"):
            package_managers.append("Python packaging")
            pyproject_path = self._find_file(
                root,
                files.get("dependencies", []),
                "pyproject.toml",
            )
            if pyproject_path:
                python_dependencies.extend(self._read_pyproject(pyproject_path))

        dependency_files = files.get("dependencies", [])
        lock_files = files.get("locks", [])
        if self._has_file(dependency_files, "environment.yml") or self._has_file(
            dependency_files,
            "environment.yaml",
        ):
            package_managers.append("conda")
        if self._has_file(dependency_files, "pipfile"):
            package_managers.append("pipenv")
        if self._has_file(lock_files, "poetry.lock"):
            package_managers.append("poetry")
        if self._has_file(lock_files, "yarn.lock"):
            package_managers.append("yarn")
        if self._has_file(lock_files, "pnpm-lock.yaml"):
            package_managers.append("pnpm")

        package_json_path = self._find_file(root, files.get("node", []), "package.json")
        if package_json_path:
            package_managers.append("npm")
            node_dependencies, node_dev_dependencies = self._read_package_json(package_json_path)

        return {
            "package_managers": sorted(set(package_managers)),
            "dependencies": {
                "python": sorted(set(python_dependencies)),
                "node": {
                    "dependencies": node_dependencies,
                    "devDependencies": node_dev_dependencies,
                },
                "system": [],
            },
        }

    def _find_file(self, root: Path, paths: list[str], filename: str) -> Path | None:
        for relative_path in paths:
            if Path(relative_path).name.lower() != filename:
                continue

            path = root / relative_path
            if path.is_file():
                return path

        return None

    def _has_file(self, paths: list[str], filename: str) -> bool:
        return any(Path(path).name.lower() == filename for path in paths)

    def _read_requirements(self, path: Path) -> list[str]:
        dependencies: list[str] = []

        for raw_line in self._read_text(path).splitlines():
            dependency = self._parse_requirement_line(raw_line)
            if dependency:
                dependencies.append(dependency)

        return sorted(set(dependencies))

    def _read_pyproject(self, path: Path) -> list[str]:
        try:
            data = tomllib.loads(self._read_text(path))
        except tomllib.TOMLDecodeError:
            return []

        dependencies: list[str] = []
        project = data.get("project", {})
        if isinstance(project, dict):
            dependencies.extend(self._dependency_list(project.get("dependencies")))
            optional = project.get("optional-dependencies", {})
            if isinstance(optional, dict):
                for values in optional.values():
                    dependencies.extend(self._dependency_list(values))

        tool = data.get("tool", {})
        poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
        if isinstance(poetry, dict):
            for section in ("dependencies", "dev-dependencies", "group"):
                values = poetry.get(section, {})
                if section == "group" and isinstance(values, dict):
                    for group in values.values():
                        if isinstance(group, dict):
                            dependencies.extend(
                                self._dependency_names(group.get("dependencies"))
                            )
                else:
                    dependencies.extend(self._dependency_names(values))

        return sorted(
            dependency
            for dependency in set(dependencies)
            if dependency.lower() != "python"
        )

    def _dependency_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []

        dependencies: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            match = re.match(r"\s*([A-Za-z0-9_.-]+)", item)
            if match:
                dependencies.append(match.group(1))
        return dependencies

    def _parse_requirement_line(self, line: str) -> str | None:
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#") or cleaned.startswith("-"):
            return None

        cleaned = cleaned.split(" #", 1)[0].strip()
        if " @ " in cleaned:
            cleaned = cleaned.split(" @ ", 1)[0].strip()

        for separator in ("==", ">=", "<=", "~=", "!=", ">", "<", "[", ";"):
            if separator in cleaned:
                cleaned = cleaned.split(separator, 1)[0].strip()

        return cleaned or None

    def _read_package_json(self, path: Path) -> tuple[list[str], list[str]]:
        try:
            data = json.loads(self._read_text(path))
        except json.JSONDecodeError:
            return [], []

        dependencies = self._dependency_names(data.get("dependencies"))
        dev_dependencies = self._dependency_names(data.get("devDependencies"))

        return dependencies, dev_dependencies

    def _dependency_names(self, value: object) -> list[str]:
        if not isinstance(value, dict):
            return []

        return sorted(str(name) for name in value)

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")
        except OSError:
            return ""
