from dataclasses import asdict
from pathlib import Path

from ci2_lab.agents.scanner_agent import ScannerAgent
from ci2_lab.models import AuditResult, ProjectInventory


class AuditorAgent:
    def __init__(self, scanner: ScannerAgent | None = None) -> None:
        self.scanner = scanner or ScannerAgent()

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
        tools = self._detect_tools(files)
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
            frameworks=[],
            scripts=[
                {"path": path, "type": "unknown", "commands": []}
                for path in files.get("scripts", [])
            ],
            documentation=documentation,
            audit=asdict(audit),
        )

        self.print_summary(inventory, files)
        return inventory

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

    def _detect_tools(self, files: dict[str, list[str]]) -> list[str]:
        tools: list[str] = []

        if any(path.endswith("Dockerfile") for path in files.get("docker", [])):
            tools.append("Docker")
        if any(path.endswith("Makefile") for path in files.get("scripts", [])):
            tools.append("Make")

        return sorted(set(tools))

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
