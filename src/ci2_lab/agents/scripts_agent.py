from pathlib import Path

from ci2_lab.models import ScanResult


class ScriptsAgent:
    def analyze(self, project_path: str | Path, scan_result: ScanResult) -> list[dict]:
        root = Path(project_path).resolve()
        scripts: list[dict] = []

        for relative_path in scan_result.files.get("scripts", []):
            path = root / relative_path
            script_type = self._detect_type(path)
            scripts.append(
                {
                    "path": relative_path,
                    "type": script_type,
                    "commands": self._extract_commands(path, script_type),
                }
            )

        return scripts

    def _detect_type(self, path: Path) -> str:
        if path.name == "Makefile":
            return "makefile"
        if path.suffix.lower() == ".sh":
            return "shell"
        return "unknown"

    def _extract_commands(self, path: Path, script_type: str) -> list[str]:
        text = self._read_text(path)
        if script_type == "shell":
            return self._extract_shell_commands(text)
        if script_type == "makefile":
            return self._extract_makefile_commands(text)
        return []

    def _extract_shell_commands(self, text: str) -> list[str]:
        commands: list[str] = []

        for line in text.splitlines():
            command = line.strip()
            if not command or command.startswith("#"):
                continue
            commands.append(command)

        return commands

    def _extract_makefile_commands(self, text: str) -> list[str]:
        commands: list[str] = []
        current_target: str | None = None

        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if raw_line.startswith("\t") and current_target:
                commands.append(f"{current_target}: {stripped}")
                continue

            if ":" in raw_line and not raw_line.startswith((" ", "\t")):
                target = raw_line.split(":", 1)[0].strip()
                if target and "=" not in target:
                    current_target = target
                continue

            current_target = None

        return commands

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")
        except OSError:
            return ""
