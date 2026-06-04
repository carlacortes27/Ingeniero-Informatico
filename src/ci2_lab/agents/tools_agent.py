from pathlib import Path


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

    def detect(
        self,
        files: dict[str, list[str]],
        dependency_result: dict[str, object],
    ) -> tuple[list[str], list[str]]:
        tools: set[str] = set()
        frameworks: set[str] = set()

        self._detect_from_files(files, tools)
        self._detect_from_dependencies(dependency_result, tools, frameworks)

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

    def _detect_from_dependencies(
        self,
        dependency_result: dict[str, object],
        tools: set[str],
        frameworks: set[str],
    ) -> None:
        dependencies = dependency_result.get("dependencies", {})
        if not isinstance(dependencies, dict):
            return

        python_packages = self._string_list(dependencies.get("python"))
        metadata = dependency_result.get("metadata", {})
        if isinstance(metadata, dict):
            python_packages.extend(self._string_list(metadata.get("python_tool_configs")))

        self._add_python_matches(set(python_packages), tools, frameworks)

        node_dependencies = dependencies.get("node", {})
        node_packages: list[str] = []
        if isinstance(node_dependencies, dict):
            for section in ("dependencies", "devDependencies"):
                node_packages.extend(self._string_list(node_dependencies.get(section)))
        if isinstance(metadata, dict):
            node_packages.extend(self._string_list(metadata.get("node_peerDependencies")))

        for package_name in node_packages:
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

    def _string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]
