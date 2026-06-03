import json
from pathlib import Path
import re
import tomllib


class ToolsAgent:
    python_tools = {
        "pytest": "pytest",
        "ruff": "ruff",
        "black": "black",
        "mypy": "mypy",
        "jupyter": "Jupyter",
        "notebook": "Jupyter",
        "ipykernel": "Jupyter",
    }
    python_frameworks = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
    }
    node_frameworks = {
        "react": "React",
        "vue": "Vue",
        "@vue/cli": "Vue",
        "@angular/core": "Angular",
        "angular": "Angular",
        "vite": "Vite",
        "express": "Express",
    }

    def detect(self, project_path: str | Path, files: dict[str, list[str]]) -> tuple[list[str], list[str]]:
        root = Path(project_path)
        tools: set[str] = set()
        frameworks: set[str] = set()

        self._detect_from_files(files, tools)
        self._detect_python_manifests(root, files, tools, frameworks)
        self._detect_node_manifests(root, files, frameworks)

        return sorted(tools), sorted(frameworks)

    def _detect_from_files(self, files: dict[str, list[str]], tools: set[str]) -> None:
        docker_files = {Path(path).name.lower() for path in files.get("docker", [])}
        script_files = {Path(path).name for path in files.get("scripts", [])}
        ci_files = [path.lower() for path in files.get("ci", [])]

        if "dockerfile" in docker_files:
            tools.add("Docker")
        if {"docker-compose.yml", "docker-compose.yaml"} & docker_files:
            tools.add("Docker Compose")
        if "Makefile" in script_files:
            tools.add("Make")
        if any(path.startswith(".github/workflows/") for path in ci_files):
            tools.add("GitHub Actions")
        if ".gitlab-ci.yml" in ci_files:
            tools.add("GitLab CI")
        if files.get("notebooks"):
            tools.add("Jupyter")

    def _detect_python_manifests(
        self,
        root: Path,
        files: dict[str, list[str]],
        tools: set[str],
        frameworks: set[str],
    ) -> None:
        for relative_path in files.get("dependencies", []):
            path = root / relative_path
            lower_name = path.name.lower()

            if lower_name == "requirements.txt":
                packages = self._read_requirements(path)
            elif lower_name == "pyproject.toml":
                packages = self._read_pyproject(path)
            else:
                continue

            self._add_python_matches(packages, tools, frameworks)

    def _detect_node_manifests(
        self,
        root: Path,
        files: dict[str, list[str]],
        frameworks: set[str],
    ) -> None:
        for relative_path in files.get("node", []):
            path = root / relative_path
            if path.name.lower() != "package.json":
                continue

            for package_name in self._read_package_json(path):
                framework = self.node_frameworks.get(package_name.lower())
                if framework:
                    frameworks.add(framework)

    def _add_python_matches(
        self,
        packages: set[str],
        tools: set[str],
        frameworks: set[str],
    ) -> None:
        for package_name in packages:
            normalized = package_name.lower()
            if normalized in self.python_tools:
                tools.add(self.python_tools[normalized])
            if normalized in self.python_frameworks:
                frameworks.add(self.python_frameworks[normalized])

    def _read_requirements(self, path: Path) -> set[str]:
        packages: set[str] = set()
        if not path.exists():
            return packages

        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.split("#", 1)[0].strip()
            if not stripped or stripped.startswith(("-", "git+", "http://", "https://")):
                continue
            packages.add(self._normalize_requirement_name(stripped))

        return packages

    def _read_pyproject(self, path: Path) -> set[str]:
        packages: set[str] = set()
        if not path.exists():
            return packages

        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            return packages

        project = data.get("project", {})
        packages.update(self._names_from_dependency_list(project.get("dependencies", [])))

        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for dependencies in optional.values():
                packages.update(self._names_from_dependency_list(dependencies))

        tool_config = data.get("tool", {})
        if isinstance(tool_config, dict):
            for tool_name in tool_config:
                packages.add(tool_name)

        poetry = tool_config.get("poetry", {}) if isinstance(tool_config, dict) else {}
        if isinstance(poetry, dict):
            for section in ("dependencies", "dev-dependencies"):
                dependencies = poetry.get(section, {})
                if isinstance(dependencies, dict):
                    packages.update(dependencies)

        return packages

    def _read_package_json(self, path: Path) -> set[str]:
        if not path.exists():
            return set()

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return set()

        packages: set[str] = set()
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            dependencies = data.get(section, {})
            if isinstance(dependencies, dict):
                packages.update(dependencies)

        return packages

    def _names_from_dependency_list(self, dependencies: object) -> set[str]:
        if not isinstance(dependencies, list):
            return set()

        return {
            self._normalize_requirement_name(dependency)
            for dependency in dependencies
            if isinstance(dependency, str)
        }

    def _normalize_requirement_name(self, requirement: str) -> str:
        match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
        if not match:
            return requirement.strip().lower()
        return match.group(1).replace("_", "-").lower()
