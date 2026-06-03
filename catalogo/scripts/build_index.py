#!/usr/bin/env python3
"""
Reconstruye catalog.json a partir de todas las fichas en fichas/.

Este fichero NUNCA se edita a mano: es el artefacto de salida de build_index.py.
Ejecutar tras cualquier adición o modificación de fichas.

Uso:
    python scripts/build_index.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CATALOG_ROOT = Path(__file__).parent.parent


def build_index() -> None:
    fichas_root = CATALOG_ROOT / "fichas"
    if not fichas_root.exists():
        print("ERROR: no existe fichas/. Ejecuta generate_fichas.py primero.", file=sys.stderr)
        sys.exit(1)

    all_fichas: list[dict] = []
    skipped = 0

    for json_file in sorted(fichas_root.rglob("*.json")):
        if json_file.name.startswith("_"):
            skipped += 1
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            data["_ficha_path"] = str(json_file.relative_to(CATALOG_ROOT)).replace("\\", "/")
            all_fichas.append(data)
        except json.JSONDecodeError as exc:
            print(f"[WARN] Error leyendo {json_file.name}: {exc}", file=sys.stderr)

    # Agrupar por proyecto para el resumen
    by_project: dict[str, int] = {}
    for f in all_fichas:
        p = f.get("proyecto", "desconocido")
        by_project[p] = by_project.get(p, 0) + 1

    index = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "total": len(all_fichas),
        "por_proyecto": by_project,
        "fichas": all_fichas,
    }

    out = CATALOG_ROOT / "catalog.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"catalog.json generado — {len(all_fichas)} fichas de {len(by_project)} proyecto(s):")
    for proj, count in sorted(by_project.items()):
        print(f"  {proj}: {count}")
    if skipped:
        print(f"  (se ignoraron {skipped} fichero(s) de auditoría _omitidas.json)")


if __name__ == "__main__":
    build_index()
