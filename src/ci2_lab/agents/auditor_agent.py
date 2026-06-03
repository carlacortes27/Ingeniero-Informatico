from dataclasses import asdict
import json
from pathlib import Path

from ci2_lab.agents.scanner_agent import ScannerAgent
from ci2_lab.agents.tools_agent import ToolsAgent
from ci2_lab.models import AuditResult, ProjectInventory


class AuditorAgent:
    def __init__(
        self,
        scanner: ScannerAgent | None = None,
        tools_agent: ToolsAgent | None = None,
    ) -> None:
        self.scanner = scanner or ScannerAgent()
        self.tools_agent = tools_agent or ToolsAgent()

    def scan(self, project_path: str | Path) -> ProjectInventory:
        root = Path(project_path).resolve()
        audit = AuditResult(is_valid=True)

        if not root.exists():
            audit.is_valid = False
            audit.errors.append(f"La ruta no existe: {root}")
            inventory = ProjectInventory(
                project_name=root.name,
                project_path=str(root),
                audit=asdict(audit),
            )
            self.print_summary(inventory)
            return inventory

        if not root.is_dir():
            audit.is_valid = False
            audit.errors.append(f"La ruta no es un directorio: {root}")
            inventory = ProjectInventory(
                project_name=root.name,
                project_path=str(root),
                audit=asdict(audit),
            )
            self.print_summary(inventory)
            return inventory

        scan_result = self.scanner.scan(root)
        files = scan_result.files

        languages = self._detect_languages(files)
        tools, frameworks = self.tools_agent.detect(root, files)
        package_managers = self._detect_package_managers(files)
        documentation = {
            "has_readme": any(
                path.lower() == "readme.md"
                or path.lower().endswith("/readme.md")
                for path in files.get("documentation", [])
            )
        }

        if not documentation["has_readme"]:
            audit.warnings.append("No se ha encontrado README.md.")

        inventory = ProjectInventory(
            project_name=scan_result.project_name,
            project_path=scan_result.project_path,
            languages=languages,
            package_managers=package_managers,
            dependencies={"python": [], "node": [], "system": []},
            tools=tools,
            frameworks=frameworks,
            scripts=[
                {"path": path, "type": "unknown", "commands": []}
                for path in files.get("scripts", [])
            ],
            documentation=documentation,
            audit=asdict(audit),
        )

        self._write_outputs(inventory)
        self.print_summary(inventory, files)
        return inventory

    def _write_outputs(self, inventory: ProjectInventory) -> None:
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        inventory_data = asdict(inventory)

        inventory_path = output_dir / "inventory.json"
        inventory_path.write_text(
            json.dumps(inventory_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        report_path = output_dir / "report.md"
        report_path.write_text(
            self._build_report(inventory),
            encoding="utf-8",
        )

    def _build_report(self, inventory: ProjectInventory) -> str:
        languages = inventory.languages or ["No detectados"]
        tools = inventory.tools or ["No detectadas"]
        readme_status = (
            "README encontrado."
            if inventory.documentation.get("has_readme")
            else "README no encontrado."
        )

        lines = [
            f"# Informe de inventario: {inventory.project_name}",
            "",
            "## Resumen",
            "",
            f"Proyecto analizado en: {inventory.project_path}",
            "",
            "## Lenguajes detectados",
            "",
            *[f"- {language}" for language in languages],
            "",
            "## Herramientas detectadas",
            "",
            *[f"- {tool}" for tool in tools],
            "",
            "## Documentacion",
            "",
            f"- {readme_status}",
        ]

        warnings = inventory.audit.get("warnings", [])
        if warnings:
            lines.extend(
                [
                    "",
                    "## Advertencias",
                    "",
                    *[f"- {warning}" for warning in warnings],
                ]
            )

        return "\n".join(lines) + "\n"

    def _detect_languages(self, files: dict[str, list[str]]) -> list[str]:
        languages: list[str] = []

        dependency_files = {Path(path).name for path in files.get("dependencies", [])}

        if files.get("python") or "requirements.txt" in dependency_files:
            languages.append("Python")
        if files.get("scripts"):
            languages.append("Bash")
        if files.get("notebooks"):
            languages.append("Jupyter Notebook")
        if files.get("node"):
            languages.append("Node.js")

        return sorted(set(languages))

    def _detect_package_managers(self, files: dict[str, list[str]]) -> list[str]:
        package_managers: list[str] = []

        dependency_files = {Path(path).name for path in files.get("dependencies", [])}

        if "requirements.txt" in dependency_files:
            package_managers.append("pip")
        if "pyproject.toml" in dependency_files:
            package_managers.append("Python packaging")
        if files.get("node"):
            package_managers.append("npm")

        return sorted(set(package_managers))

    def print_summary(
        self,
        inventory: ProjectInventory,
        files: dict[str, list[str]] | None = None,
    ) -> None:
        print(f"Analizando proyecto: {inventory.project_name}")
        print()

        audit = inventory.audit
        if audit.get("errors"):
            print("Errores:")
            for error in audit["errors"]:
                print(f"- {error}")
            return

        print("[1/2] Scanner ejecutado correctamente.")
        print("[2/2] Auditoria basica completada.")
        print()
        print("Resumen:")
        print(f"- Ruta: {inventory.project_path}")
        print(f"- Lenguajes: {', '.join(inventory.languages) or 'No detectados'}")
        print(f"- Herramientas: {', '.join(inventory.tools) or 'No detectadas'}")
        print(f"- Frameworks: {', '.join(inventory.frameworks) or 'No detectados'}")
        print(f"- README: {'si' if inventory.documentation.get('has_readme') else 'no'}")

        if files:
            total_files = sum(len(paths) for paths in files.values())
            print(f"- Archivos relevantes: {total_files}")
            for category, paths in sorted(files.items()):
                print(f"  - {category}: {len(paths)}")

        if audit.get("warnings"):
            print()
            print("Advertencias:")
            for warning in audit["warnings"]:
                print(f"- {warning}")
