from dataclasses import asdict
import json
from pathlib import Path

from ci2_lab.agents.dependency_agent import DependencyAgent
from ci2_lab.agents.documentation_agent import DocumentationAgent
from ci2_lab.agents.inventory_agent import InventoryAgent
from ci2_lab.agents.language_agent import LanguageAgent
from ci2_lab.agents.report_agent import ReportAgent
from ci2_lab.agents.scanner_agent import ScannerAgent
from ci2_lab.agents.scripts_agent import ScriptsAgent
from ci2_lab.agents.tools_agent import ToolsAgent
from ci2_lab.models import AuditResult, ProjectInventory


class AuditorAgent:
    def __init__(
        self,
        scanner: ScannerAgent | None = None,
        dependency_agent: DependencyAgent | None = None,
        documentation_agent: DocumentationAgent | None = None,
        language_agent: LanguageAgent | None = None,
        scripts_agent: ScriptsAgent | None = None,
        tools_agent: ToolsAgent | None = None,
        inventory_agent: InventoryAgent | None = None,
        report_agent: ReportAgent | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        self.scanner = scanner or ScannerAgent()
        self.dependency_agent = dependency_agent or DependencyAgent()
        self.documentation_agent = documentation_agent or DocumentationAgent()
        self.language_agent = language_agent or LanguageAgent()
        self.scripts_agent = scripts_agent or ScriptsAgent()
        self.tools_agent = tools_agent or ToolsAgent()
        self.inventory_agent = inventory_agent or InventoryAgent()
        self.report_agent = report_agent or ReportAgent()
        self.output_dir = Path(output_dir) if output_dir is not None else None

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

        dependency_result = self.dependency_agent.analyze(root, scan_result)
        documentation = self.documentation_agent.analyze(root, scan_result)
        languages = self.language_agent.detect(scan_result)
        scripts = self.scripts_agent.analyze(root, scan_result)
        tools, frameworks = self.tools_agent.detect(root, files)

        if not documentation["has_readme"]:
            audit.warnings.append("No se ha encontrado README.md o README.rst.")

        inventory = ProjectInventory(
            project_name=scan_result.project_name,
            project_path=scan_result.project_path,
            languages=languages,
            package_managers=dependency_result["package_managers"],
            dependencies=dependency_result["dependencies"],
            tools=tools,
            frameworks=frameworks,
            scripts=scripts,
            documentation=documentation,
            audit=asdict(audit),
        )

        self._audit_inventory(inventory, files, audit)
        inventory.audit = asdict(audit)

        if self.output_dir is not None and audit.is_valid:
            self._write_outputs(inventory)
        self.print_summary(inventory, files)
        return inventory

    def _write_outputs(self, inventory: ProjectInventory) -> None:
        if self.output_dir is None:
            return
        self.inventory_agent.save(inventory, self.output_dir)
        self.report_agent.save(inventory, self.output_dir)

    def _audit_inventory(
        self,
        inventory: ProjectInventory,
        files: dict[str, list[str]],
        audit: AuditResult,
    ) -> None:
        if not inventory.project_name:
            audit.is_valid = False
            audit.errors.append("Falta el nombre del proyecto.")

        for field_name in ("languages", "package_managers", "tools", "frameworks"):
            values = getattr(inventory, field_name)
            if len(values) != len(set(values)):
                audit.is_valid = False
                audit.errors.append(f"El campo {field_name} contiene duplicados.")

        dependency_files = {
            Path(path).name.lower()
            for path in files.get("dependencies", [])
        }
        if "requirements.txt" in dependency_files and "pip" not in inventory.package_managers:
            audit.warnings.append(
                "requirements.txt encontrado, pero pip no fue detectado."
            )
        if files.get("node") and "npm" not in inventory.package_managers:
            audit.warnings.append(
                "package.json encontrado, pero npm no fue detectado."
            )

        readme_found = any(
            Path(path).name.lower() in {"readme.md", "readme.rst"}
            for path in files.get("documentation", [])
        )
        if readme_found != bool(inventory.documentation.get("has_readme")):
            audit.is_valid = False
            audit.errors.append(
                "El resultado de documentacion no coincide con los archivos escaneados."
            )

        try:
            json.dumps(asdict(inventory))
        except (TypeError, ValueError):
            audit.is_valid = False
            audit.errors.append("El inventario no se puede serializar a JSON.")

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
