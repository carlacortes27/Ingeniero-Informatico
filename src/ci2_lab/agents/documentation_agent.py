from pathlib import Path
import unicodedata

from ci2_lab.agents.scanner_agent import ScannerAgent
from ci2_lab.models import ScanResult


class DocumentationAgent:
    expected_sections = {
        "installation": ("installation", "install", "instalacion", "instalar"),
        "usage": ("usage", "use", "uso", "utilizacion", "usar"),
        "examples": ("examples", "example", "ejemplos", "ejemplo"),
    }

    def __init__(self, scanner: ScannerAgent | None = None) -> None:
        self.scanner = scanner or ScannerAgent()

    def analyze(
        self,
        project_path: str | Path,
        scan_result: ScanResult | None = None,
    ) -> dict:
        root = Path(project_path).resolve()
        scan_result = scan_result or self.scanner.scan(root)
        documentation_files = scan_result.files.get("documentation", [])

        readme_path = self._find_readme(root, documentation_files)
        has_docs_folder = (root / "docs").is_dir() or any(
            Path(path).parts and Path(path).parts[0].lower() == "docs"
            for path in documentation_files
        )

        readme_text = self._read_text(readme_path) if readme_path else ""
        found_sections = self._detect_sections(readme_text)
        missing_sections = [
            section
            for section in ("installation", "usage", "examples")
            if section not in found_sections
        ]

        return {
            "has_readme": readme_path is not None,
            "has_docs_folder": has_docs_folder,
            "has_installation_section": "installation" in found_sections,
            "has_usage_section": "usage" in found_sections,
            "has_examples_section": "examples" in found_sections,
            "missing_sections": missing_sections,
        }

    def _find_readme(self, root: Path, documentation_files: list[str]) -> Path | None:
        readme_names = {"readme.md", "readme.rst"}
        candidates = [
            path
            for path in documentation_files
            if Path(path).name.lower() in readme_names
        ]

        candidates.sort(key=lambda path: (len(Path(path).parts), path.lower()))

        for relative_path in candidates:
            path = root / relative_path
            if path.is_file():
                return path

        return None

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")
        except OSError:
            return ""

    def _detect_sections(self, text: str) -> set[str]:
        normalized_lines = [
            self._normalize(line).strip(" #:=`*-")
            for line in text.splitlines()
        ]

        sections: set[str] = set()
        for line in normalized_lines:
            if not line:
                continue
            for section, keywords in self.expected_sections.items():
                if any(keyword in line.split() for keyword in keywords):
                    sections.add(section)

        return sections

    def _normalize(self, value: str) -> str:
        without_accents = unicodedata.normalize("NFKD", value)
        return "".join(
            character
            for character in without_accents
            if not unicodedata.combining(character)
        ).lower()
