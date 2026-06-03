from pathlib import Path

from ci2_lab.agents.scanner_agent import ScannerAgent


def touch(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scanner_classifies_relevant_files(tmp_path) -> None:
    touch(tmp_path / "src" / "main.py")
    touch(tmp_path / "requirements.txt")
    touch(tmp_path / "pyproject.toml")
    touch(tmp_path / "setup.py")
    touch(tmp_path / "setup.cfg")
    touch(tmp_path / "environment.yml")
    touch(tmp_path / "Pipfile")
    touch(tmp_path / "poetry.lock")
    touch(tmp_path / "package.json", "{}")
    touch(tmp_path / "package-lock.json", "{}")
    touch(tmp_path / "yarn.lock")
    touch(tmp_path / "pnpm-lock.yaml")
    touch(tmp_path / "Dockerfile")
    touch(tmp_path / "docker-compose.yml")
    touch(tmp_path / "Makefile")
    touch(tmp_path / "scripts" / "run.sh")
    touch(tmp_path / "README.md")
    touch(tmp_path / "README.rst")
    touch(tmp_path / "INSTALL.md")
    touch(tmp_path / "CONTRIBUTING.md")
    touch(tmp_path / "CHANGELOG.md")
    touch(tmp_path / "docs" / "index.md")
    touch(tmp_path / "analysis.ipynb")
    touch(tmp_path / "config" / "app.yaml")
    touch(tmp_path / ".github" / "workflows" / "test.yml")
    touch(tmp_path / ".gitlab-ci.yml")

    result = ScannerAgent().scan(tmp_path)

    assert result.project_name == tmp_path.name
    assert result.project_path == str(tmp_path.resolve())
    assert result.files["python"] == ["src/main.py"]
    assert result.files["dependencies"] == [
        "Pipfile",
        "environment.yml",
        "pyproject.toml",
        "requirements.txt",
        "setup.cfg",
        "setup.py",
    ]
    assert result.files["node"] == ["package.json"]
    assert result.files["locks"] == [
        "package-lock.json",
        "pnpm-lock.yaml",
        "poetry.lock",
        "yarn.lock",
    ]
    assert result.files["docker"] == ["Dockerfile", "docker-compose.yml"]
    assert result.files["scripts"] == ["Makefile", "scripts/run.sh"]
    assert result.files["documentation"] == [
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "INSTALL.md",
        "README.md",
        "README.rst",
        "docs/index.md",
    ]
    assert result.files["notebooks"] == ["analysis.ipynb"]
    assert result.files["config"] == ["config/app.yaml"]
    assert result.files["ci"] == [
        ".github/workflows/test.yml",
        ".gitlab-ci.yml",
    ]


def test_scanner_ignores_irrelevant_directories(tmp_path) -> None:
    ignored_dirs = [
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
    ]

    for directory in ignored_dirs:
        touch(tmp_path / directory / "ignored.py")

    touch(tmp_path / "main.py")

    result = ScannerAgent().scan(tmp_path)

    assert result.files["python"] == ["main.py"]


def test_scanner_returns_only_relative_paths(tmp_path) -> None:
    touch(tmp_path / "src" / "nested" / "module.py")
    touch(tmp_path / "docs" / "guide.md")

    result = ScannerAgent().scan(tmp_path)

    all_paths = [
        path
        for paths in result.files.values()
        for path in paths
    ]

    assert sorted(all_paths) == ["docs/guide.md", "src/nested/module.py"]
    assert all(not Path(path).is_absolute() for path in all_paths)
