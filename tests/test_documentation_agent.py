from ci2_lab.agents.documentation_agent import DocumentationAgent
from ci2_lab.agents.scanner_agent import ScannerAgent


def test_documentation_agent_detects_readme_docs_and_sections(tmp_path) -> None:
    (tmp_path / "README.md").write_text(
        """
# Demo
## Installation
## Usage
## Examples
## Tests
## Docker
## Architecture
## Dependencies
""".strip(),
        encoding="utf-8",
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide", encoding="utf-8")

    scan_result = ScannerAgent().scan(tmp_path)
    result = DocumentationAgent().analyze(tmp_path, scan_result)

    assert result["has_readme"] is True
    assert result["has_docs_folder"] is True
    assert result["missing_sections"] == []
    assert all(
        result[key] is True
        for key in (
            "has_installation_section",
            "has_usage_section",
            "has_examples_section",
            "has_tests_section",
            "has_docker_section",
            "has_architecture_section",
            "has_dependencies_section",
        )
    )


def test_documentation_agent_reports_missing_documentation(tmp_path) -> None:
    result = DocumentationAgent().analyze(tmp_path)

    assert result["has_readme"] is False
    assert result["has_docs_folder"] is False
    assert set(result["missing_sections"]) == {
        "installation",
        "usage",
        "examples",
        "tests",
        "docker",
        "architecture",
        "dependencies",
    }
