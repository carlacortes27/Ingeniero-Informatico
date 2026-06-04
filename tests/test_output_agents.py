import json

from ci2_lab.agents.inventory_agent import InventoryAgent
from ci2_lab.agents.report_agent import ReportAgent
from ci2_lab.models import ProjectInventory


def build_inventory() -> ProjectInventory:
    return ProjectInventory(
        project_name="demo",
        project_path="/demo",
        languages=["Python"],
        package_managers=["pip"],
        dependencies={
            "python": ["fastapi"],
            "node": {"dependencies": ["react"], "devDependencies": ["vite"]},
            "system": [],
        },
        tools=["Docker"],
        frameworks=["FastAPI"],
        scripts=[{"path": "run.sh", "type": "execution", "commands": []}],
        documentation={"has_readme": True},
        audit={"is_valid": True, "errors": [], "warnings": []},
    )


def test_inventory_agent_writes_structured_json(tmp_path) -> None:
    output_path = InventoryAgent().save(build_inventory(), tmp_path / "nested")

    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path == tmp_path / "nested" / "inventory.json"
    assert data["project_name"] == "demo"
    assert data["dependencies"]["node"]["dependencies"] == ["react"]


def test_report_agent_writes_relevant_sections(tmp_path) -> None:
    output_path = ReportAgent().save(build_inventory(), tmp_path / "nested")
    report = output_path.read_text(encoding="utf-8")

    assert "# Informe de inventario: demo" in report
    assert "## Frameworks" in report
    assert "- FastAPI" in report
    assert "## Dependencias" in report
    assert "- node: react, vite" in report
    assert "## Scripts" in report
    assert "- run.sh" in report
