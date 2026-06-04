from pathlib import Path

from ci2_lab.models import ScanResult


class LanguageAgent:
    def detect(self, scan_result: ScanResult) -> list[str]:
        files = scan_result.files
        languages: set[str] = set()

        if files.get("python") or files.get("dependencies"):
            languages.add("Python")
        if files.get("scripts"):
            languages.add("Bash")
        if files.get("notebooks"):
            languages.add("Jupyter Notebook")
        if files.get("node"):
            languages.add("Node.js")
        if self._has_yaml_config(files.get("config", [])):
            languages.add("YAML")

        return sorted(languages)

    def _has_yaml_config(self, paths: list[str]) -> bool:
        return any(Path(path).suffix.lower() in {".yml", ".yaml"} for path in paths)
