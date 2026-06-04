import json

from ci2_lab.agents.dependency_agent import DependencyAgent
from ci2_lab.agents.scanner_agent import ScannerAgent


def test_dependency_agent_extracts_python_and_node_dependencies(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "requests==2.32\npytest>=8\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["fastapi>=0.100"]
optional-dependencies.dev = ["ruff"]
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "^18"},
                "devDependencies": {"vite": "^5"},
            }
        ),
        encoding="utf-8",
    )

    scan_result = ScannerAgent().scan(tmp_path)
    result = DependencyAgent().analyze(tmp_path, scan_result)

    assert result["package_managers"] == ["Python packaging", "npm", "pip"]
    assert result["dependencies"]["python"] == [
        "fastapi",
        "pytest",
        "requests",
        "ruff",
    ]
    assert result["dependencies"]["node"] == {
        "dependencies": ["react"],
        "devDependencies": ["vite"],
    }


def test_dependency_agent_detects_package_managers_from_manifests(tmp_path) -> None:
    for filename in (
        "environment.yml",
        "Pipfile",
        "poetry.lock",
        "yarn.lock",
        "pnpm-lock.yaml",
    ):
        (tmp_path / filename).write_text("", encoding="utf-8")

    scan_result = ScannerAgent().scan(tmp_path)
    result = DependencyAgent().analyze(tmp_path, scan_result)

    assert result["package_managers"] == [
        "conda",
        "pipenv",
        "pnpm",
        "poetry",
        "yarn",
    ]


def test_dependency_agent_handles_invalid_manifests(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text("invalid = [", encoding="utf-8")
    (tmp_path / "package.json").write_text("{invalid", encoding="utf-8")

    scan_result = ScannerAgent().scan(tmp_path)
    result = DependencyAgent().analyze(tmp_path, scan_result)

    assert result["dependencies"]["python"] == []
    assert result["dependencies"]["node"] == {
        "dependencies": [],
        "devDependencies": [],
    }
