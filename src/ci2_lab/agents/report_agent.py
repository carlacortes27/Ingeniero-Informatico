from pathlib import Path

from ci2_lab.models import ProjectInventory


class ReportAgent:
    def save(
        self,
        inventory: ProjectInventory,
        output_dir: str | Path = "outputs",
    ) -> Path:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_path = output_path / "report.md"
        report_path.write_text(
            self._build_report(inventory),
            encoding="utf-8",
        )

        return report_path

    def _build_report(self, inventory: ProjectInventory) -> str:
        languages = inventory.languages or ["No detectados"]
        tools = inventory.tools or ["No detectadas"]
        frameworks = inventory.frameworks or ["No detectados"]
        package_managers = inventory.package_managers or ["No detectados"]
        readme_status = (
            "README encontrado."
            if inventory.documentation.get("has_readme")
            else "README no encontrado."
        )

        lines = [
            f"# Informe de inventario: {inventory.project_name}",
            "",
            "## Lenguajes",
            "",
            *[f"- {language}" for language in languages],
            "",
            "## Herramientas",
            "",
            *[f"- {tool}" for tool in tools],
            "",
            "## Frameworks",
            "",
            *[f"- {framework}" for framework in frameworks],
            "",
            "## Gestores de paquetes",
            "",
            *[f"- {manager}" for manager in package_managers],
            "",
            "## Dependencias",
            "",
            *self._dependency_lines(inventory.dependencies),
            "",
            "## Scripts",
            "",
            *self._script_lines(inventory.scripts),
            "",
            "## Documentacion",
            "",
            f"- {readme_status}",
        ]

        errors = inventory.audit.get("errors", [])
        if errors:
            lines.extend(
                [
                    "",
                    "## Errores",
                    "",
                    *[f"- {error}" for error in errors],
                ]
            )

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

    def _dependency_lines(self, dependencies: dict[str, object]) -> list[str]:
        lines: list[str] = []
        for ecosystem, values in sorted(dependencies.items()):
            if isinstance(values, dict):
                names = [
                    str(name)
                    for group in values.values()
                    if isinstance(group, list)
                    for name in group
                ]
            elif isinstance(values, list):
                names = [str(name) for name in values]
            else:
                names = []

            lines.append(f"- {ecosystem}: {', '.join(sorted(set(names))) or 'Ninguna'}")
        return lines or ["- Ninguna"]

    def _script_lines(self, scripts: list[dict[str, object]]) -> list[str]:
        return [
            f"- {script.get('path', 'Ruta desconocida')}"
            for script in scripts
        ] or ["- Ninguno"]
