from ci2_lab.agents.auditor_agent import AuditorAgent


def test_auditor_delegates_to_implemented_agents_without_writing_by_default(
    tmp_path,
    monkeypatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "requirements.txt").write_text(
        "fastapi\npytest\n",
        encoding="utf-8",
    )
    (project / "README.md").write_text(
        "# Demo\n## Installation\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    inventory = AuditorAgent().scan(project)

    assert inventory.dependencies["python"] == ["fastapi", "pytest"]
    assert inventory.package_managers == ["pip"]
    assert inventory.frameworks == ["FastAPI"]
    assert inventory.tools == ["pytest"]
    assert inventory.documentation["has_installation_section"] is True
    assert inventory.languages == []
    assert inventory.scripts == []
    assert not (tmp_path / "outputs").exists()


def test_auditor_writes_outputs_when_configured(tmp_path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    output_dir = tmp_path / "result"

    AuditorAgent(output_dir=output_dir).scan(project)

    assert (output_dir / "inventory.json").is_file()
    assert (output_dir / "report.md").is_file()


def test_auditor_rejects_incoherent_agent_results(tmp_path) -> None:
    class IncorrectDocumentationAgent:
        def analyze(self, project_path, scan_result):
            return {"has_readme": False}

    project = tmp_path / "project"
    project.mkdir()
    (project / "README.md").write_text("# Demo", encoding="utf-8")
    output_dir = tmp_path / "result"

    inventory = AuditorAgent(
        documentation_agent=IncorrectDocumentationAgent(),
        output_dir=output_dir,
    ).scan(project)

    assert inventory.audit["is_valid"] is False
    assert "no coincide" in inventory.audit["errors"][0]
    assert not output_dir.exists()
