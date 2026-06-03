import json

from ci2_lab.agents.auditor_agent import AuditorAgent


def test_detects_python_tools_and_frameworks_from_pyproject(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["fastapi>=0.100", "pytest", "ruff"]

[tool.black]
line-length = 88
""".strip(),
        encoding="utf-8",
    )

    inventory = AuditorAgent().scan(tmp_path)

    assert {"pytest", "ruff", "black"} <= set(inventory.tools)
    assert "FastAPI" in inventory.frameworks


def test_detects_python_tools_and_frameworks_from_requirements(tmp_path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "flask==3.0.0\nblack>=24\n",
        encoding="utf-8",
    )

    inventory = AuditorAgent().scan(tmp_path)

    assert "black" in inventory.tools
    assert "Flask" in inventory.frameworks


def test_detects_node_frameworks_from_package_json(tmp_path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {
                    "react": "^18.0.0",
                    "vite": "^5.0.0",
                    "express": "^4.0.0",
                }
            }
        ),
        encoding="utf-8",
    )

    inventory = AuditorAgent().scan(tmp_path)

    assert {"React", "Vite", "Express"} <= set(inventory.frameworks)


def test_detects_infra_and_ci_tools_from_files(tmp_path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "test.yml").write_text("name: test\n", encoding="utf-8")
    (tmp_path / ".gitlab-ci.yml").write_text("test: {}\n", encoding="utf-8")

    inventory = AuditorAgent().scan(tmp_path)

    assert {
        "Docker",
        "Docker Compose",
        "Make",
        "GitHub Actions",
        "GitLab CI",
    } <= set(inventory.tools)
