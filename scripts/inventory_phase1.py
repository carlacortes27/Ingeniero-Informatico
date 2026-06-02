#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
RAW_PROJECTS_DIR = ROOT / "projects" / "raw"
INVENTORY_DIR = ROOT / "inventory"
TOOLS_DIR = INVENTORY_DIR / "tools"
INDEX_DIR = INVENTORY_DIR / "index"

DETECTION_SIGNALS = {
    "README.md": "Has project documentation",
    "main.py": "Has a Python entry point",
    "app.py": "Has an application entry point",
    "train.py": "Has a training entry point",
    "finetune.py": "Has a fine-tuning entry point",
    "predict.py": "Has a prediction entry point",
    "inference.py": "Has an inference entry point",
    "evaluate.py": "Has an evaluation entry point",
    "preprocess.py": "Has a preprocessing entry point",
    "postprocess.py": "Has a postprocessing entry point",
    "run.sh": "Has an execution script",
    "submit.sh": "Has a submission script",
    "requirements.txt": "Has Python dependencies",
    "pyproject.toml": "Has Python project metadata",
    "setup.py": "Has Python package metadata",
    "environment.yml": "Has Conda environment metadata",
    "Dockerfile": "Has container metadata",
    "Makefile": "Has automation commands",
}

ENTRYPOINT_FILES = {
    "main.py",
    "app.py",
    "train.py",
    "finetune.py",
    "predict.py",
    "inference.py",
    "evaluate.py",
    "preprocess.py",
    "postprocess.py",
    "run.sh",
    "submit.sh",
}

DEPENDENCY_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "environment.yml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
}

SPECIAL_DIRS = {
    "docs": "Has a docs directory",
    "examples": "Has an examples directory",
    "tests": "Has a tests directory",
    "scripts": "Has a scripts directory",
    "src": "Has a source directory",
    "notebooks": "Has notebooks",
}


@dataclass
class ToolCandidate:
    tool_id: str
    name: str
    source_project: str
    source_paths: list[str]
    evidence: list[str]
    short_description: str
    confidence: str
    status: str


def slugify(value: str) -> str:
    normalized = []
    for char in value.lower():
        if char.isalnum():
            normalized.append(char)
        elif normalized and normalized[-1] != "_":
            normalized.append("_")
    slug = "".join(normalized).strip("_")
    return slug or "tool"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_structure() -> None:
    directories = [
        RAW_PROJECTS_DIR,
        TOOLS_DIR,
        INVENTORY_DIR / "capabilities",
        INDEX_DIR,
        INVENTORY_DIR / "audit",
        ROOT / "agents",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def detect_projects(project_arg: str | None) -> list[Path]:
    if project_arg:
        project_path = (ROOT / project_arg).resolve() if not Path(project_arg).is_absolute() else Path(project_arg)
        if not project_path.exists() or not project_path.is_dir():
            raise FileNotFoundError(f"Project path not found: {project_arg}")
        return [project_path]

    if not RAW_PROJECTS_DIR.exists():
        return []

    return sorted(path for path in RAW_PROJECTS_DIR.iterdir() if path.is_dir())


def iter_project_files(project_dir: Path) -> Iterable[Path]:
    for path in project_dir.rglob("*"):
        if ".git" in path.parts:
            continue
        yield path


def collect_signals(project_dir: Path) -> tuple[list[str], list[str]]:
    evidence: list[str] = []
    source_paths: list[str] = []

    for path in iter_project_files(project_dir):
        relative = path.relative_to(project_dir).as_posix()
        name = path.name

        if name in DETECTION_SIGNALS:
            evidence.append(f"{relative}: {DETECTION_SIGNALS[name]}")
            source_paths.append(relative)

        if path.is_dir() and name in SPECIAL_DIRS:
            evidence.append(f"{relative}/: {SPECIAL_DIRS[name]}")
            source_paths.append(relative + "/")

        if path.suffix == ".sbatch":
            evidence.append(f"{relative}: Has a SLURM batch script")
            source_paths.append(relative)

        if relative.startswith("notebooks/") and path.suffix == ".ipynb":
            evidence.append(f"{relative}: Has a notebook")
            source_paths.append(relative)

    unique_paths = sorted(set(source_paths))
    unique_evidence = sorted(set(evidence))
    return unique_paths, unique_evidence


def infer_name(project_dir: Path, source_paths: list[str]) -> str:
    preferred = [path for path in source_paths if Path(path).name in ENTRYPOINT_FILES]
    if preferred:
        return Path(preferred[0]).stem.replace("_", " ").title()
    return project_dir.name.replace("_", " ").replace("-", " ").title()


def detect_candidate(project_dir: Path) -> ToolCandidate | None:
    source_paths, evidence = collect_signals(project_dir)
    if len(evidence) < 2:
        return None

    name = infer_name(project_dir, source_paths)
    tool_id = slugify(project_dir.name)
    confidence = "medium" if len(evidence) < 5 else "high"

    return ToolCandidate(
        tool_id=tool_id,
        name=name,
        source_project=project_dir.name,
        source_paths=source_paths,
        evidence=evidence,
        short_description="Detected reusable tool candidate from a local project.",
        confidence=confidence,
        status="incomplete",
    )


def render_tool_yaml(candidate: ToolCandidate) -> str:
    source_paths = "\n".join(f"  - {path}" for path in candidate.source_paths) or "  - ."
    evidence = "\n".join(
        "      - file: {file}\n        reason: {reason}".format(
            file=item.split(": ", 1)[0],
            reason=item.split(": ", 1)[1],
        )
        for item in candidate.evidence[:5]
    ) or "      - file: unknown\n        reason: insufficient evidence"
    documentation_sources = "\n".join(f"    - {item.split(': ', 1)[0]}" for item in candidate.evidence[:5]) or "    - unknown"
    timestamp = now_iso()

    return f"""tool_id: {candidate.tool_id}
name: {candidate.name}
short_description: {candidate.short_description}
long_description: Minimal inventory record generated during phase 1 detection.
source_project: {candidate.source_project}
source_paths:
{source_paths}
category: unknown
capabilities:
  - id: unknown
    confidence: low
    evidence:
{evidence}
languages: []
dependencies:
  python: []
  system: []
execution:
  local: true
  gpu: false
  slurm: false
  docker: false
  conda: false
inputs: []
outputs: []
usage_examples: []
documentation:
  sources:
{documentation_sources}
  quality: low
status: {candidate.status}
confidence: {candidate.confidence}
created_at: {timestamp}
updated_at: {timestamp}
review:
  audited: false
  audit_status: pending
  auditor_notes: Pending audit.
"""


def render_tool_readme(candidate: ToolCandidate) -> str:
    evidence_lines = "\n".join(f"- `{item}`" for item in candidate.evidence) or "- No evidence captured."
    return f"""# {candidate.name}

## Descripcion

Registro minimo generado automaticamente durante la Fase 1 del inventario.

## Capacidades

- `unknown` con confianza baja hasta clasificacion posterior.

## Entradas

- Pendiente de documentar.

## Salidas

- Pendiente de documentar.

## Dependencias

- Pendiente de extraer.

## Modo de ejecucion

- Local: si
- GPU: no detectado
- SLURM: no detectado
- Docker: no detectado
- Conda: no detectado

## Ejemplo de uso

- Pendiente de documentar.

## Evidencias utilizadas

{evidence_lines}

## Estado de documentacion

- Calidad actual: baja
- Estado: {candidate.status}
- Confianza: {candidate.confidence}

## Limitaciones conocidas

- Ficha generada con heuristicas basicas.
- Requiere enriquecimiento en fases posteriores.
"""


def write_tool(candidate: ToolCandidate, project_dir: Path) -> dict:
    tool_dir = TOOLS_DIR / candidate.tool_id
    source_dir = tool_dir / "source"
    docs_dir = tool_dir / "docs"
    examples_dir = tool_dir / "examples"
    tests_dir = tool_dir / "tests"

    for directory in (source_dir, docs_dir, examples_dir, tests_dir):
        directory.mkdir(parents=True, exist_ok=True)

    manifest_path = tool_dir / "tool.yaml"
    readme_path = tool_dir / "README.md"
    marker_path = docs_dir / "SOURCE_PROJECT.txt"

    manifest_path.write_text(render_tool_yaml(candidate), encoding="utf-8")
    readme_path.write_text(render_tool_readme(candidate), encoding="utf-8")
    marker_path.write_text(
        f"Original project path: {project_dir}\nPhase 1 keeps the original project in place and does not copy its files.\n",
        encoding="utf-8",
    )

    return {
        "tool_id": candidate.tool_id,
        "name": candidate.name,
        "capabilities": ["unknown"],
        "status": candidate.status,
        "confidence": candidate.confidence,
        "path": f"inventory/tools/{candidate.tool_id}",
    }


def write_tools_index(entries: list[dict]) -> None:
    index_path = INDEX_DIR / "tools_index.json"
    index_path.write_text(json.dumps(entries, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 inventory builder")
    parser.add_argument("--project", help="Optional single project path to analyze")
    parser.add_argument("--clean", action="store_true", help="Remove previous generated tool folders before running")
    args = parser.parse_args()

    ensure_structure()

    if args.clean and TOOLS_DIR.exists():
        shutil.rmtree(TOOLS_DIR)
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    projects = detect_projects(args.project)
    entries: list[dict] = []

    for project_dir in projects:
        candidate = detect_candidate(project_dir)
        if candidate is None:
            continue
        entries.append(write_tool(candidate, project_dir))

    write_tools_index(sorted(entries, key=lambda item: item["tool_id"]))
    print(f"Generated {len(entries)} tool record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
