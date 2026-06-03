from pathlib import Path

from ci2_lab.models import ProjectInventory


class ReportAgent:
    def save(
        self,
        inventory: ProjectInventory,
        output_dir: str | Path = "outputs",
    ) -> Path:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        report_path = output_path / "report.md"
        report_path.write_text(
            self._build_report(inventory),
            encoding="utf-8",
        )

        return report_path

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
            "## Lenguajes",
            "",
            *[f"- {language}" for language in languages],
            "",
            "## Herramientas",
            "",
            *[f"- {tool}" for tool in tools],
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
