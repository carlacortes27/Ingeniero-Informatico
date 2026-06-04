#!/usr/bin/env python3
"""
Script de uso único: rellena el campo que_hace de las fichas a partir
de las descripciones verificadas leyendo el código fuente.
Ejecutar una sola vez; se puede borrar después.
"""
import json
from pathlib import Path

FICHAS_DIR = Path(__file__).parent.parent / "fichas" / "ci2-lab-agent"

DESCRIPCIONES: dict[str, str] = {
    # --- models.py ---
    "scanresult": (
        "Dataclass que almacena el resultado de un escaneo de proyecto: nombre del "
        "proyecto, ruta absoluta y un mapa de ficheros clasificados por categoría "
        "(python, dependencias, docker, scripts, documentación, notebooks, config)."
    ),
    "auditresult": (
        "Dataclass que recoge el resultado de una auditoría: flag de validez booleano, "
        "lista de errores bloqueantes, lista de advertencias y lista de campos que "
        "fueron corregidos automáticamente."
    ),
    "projectinventory": (
        "Dataclass central que agrega el inventario completo de un proyecto: lenguajes "
        "detectados, gestores de paquetes, dependencias (Python y Node), herramientas, "
        "frameworks, scripts, estado de documentación y resultado de auditoría."
    ),
    # --- scanner_agent.py ---
    "scanneragent": (
        "Agente que recorre recursivamente un directorio de proyecto y clasifica cada "
        "fichero por tipo (python, dependencias, docker, scripts, documentación, "
        "notebooks, config), ignorando carpetas de sistema (.git, .venv, node_modules, "
        "etc.). Devuelve un ScanResult con el mapa completo de ficheros por categoría."
    ),
    "scanneragent_scan": (
        "Recorre el directorio raíz del proyecto, ignora carpetas de sistema y clasifica "
        "todos los ficheros encontrados. Devuelve un ScanResult con el nombre del "
        "proyecto, su ruta y el mapa de ficheros agrupados por categoría."
    ),
    # --- auditor_agent.py ---
    "auditoragent": (
        "Agente orquestador que coordina el análisis completo de un proyecto: instancia "
        "y ejecuta ScannerAgent, DependencyAgent, DocumentationAgent, InventoryAgent y "
        "ReportAgent en secuencia, produciendo un ProjectInventory completo y "
        "escribiendo los resultados en outputs/."
    ),
    "auditoragent_scan": (
        "Valida la ruta del proyecto, coordina los agentes especializados y construye "
        "un ProjectInventory con lenguajes, herramientas, dependencias y documentación "
        "detectados. Escribe inventory.json y report.md en outputs/ y muestra el "
        "resumen por consola. Devuelve el ProjectInventory resultante."
    ),
    "auditoragent_print_summary": (
        "Imprime por consola un resumen legible del inventario: ruta del proyecto, "
        "lenguajes detectados, herramientas, presencia de README, número total de "
        "ficheros por categoría y lista de advertencias si las hay."
    ),
    # --- dependency_agent.py ---
    "dependencyagent": (
        "Agente que analiza los ficheros de dependencias de un proyecto "
        "(requirements.txt, pyproject.toml, package.json) y extrae la lista de "
        "paquetes Python y Node junto con los gestores de paquetes presentes."
    ),
    "dependencyagent_analyze": (
        "Lee los ficheros de dependencias presentes en el ScanResult y devuelve un "
        "diccionario con los gestores de paquetes detectados (pip, npm, Python "
        "packaging) y las listas de dependencias Python y Node (dependencias de "
        "producción y de desarrollo por separado)."
    ),
    # --- documentation_agent.py ---
    "documentationagent": (
        "Agente que analiza la documentación de un proyecto: localiza el README "
        "(md o rst), comprueba si existe carpeta docs/ y verifica la presencia de "
        "las secciones estándar installation, usage y examples, con soporte para "
        "títulos en español e inglés."
    ),
    "documentationagent_analyze": (
        "Localiza el README del proyecto, detecta si existe carpeta docs/ y comprueba "
        "qué secciones estándar (installation, usage, examples) contiene el README. "
        "Devuelve un diccionario con flags booleanos por sección y la lista de "
        "secciones ausentes."
    ),
    # --- inventory_agent.py ---
    "inventoryagent": (
        "Agente que serializa un ProjectInventory completo a un fichero JSON "
        "inventory.json en el directorio de salida indicado."
    ),
    "inventoryagent_save": (
        "Serializa el ProjectInventory recibido como JSON con indentación de 2 espacios "
        "y lo escribe en <output_dir>/inventory.json (por defecto outputs/). Crea el "
        "directorio si no existe. Devuelve la ruta del fichero generado."
    ),
    # --- report_agent.py ---
    "reportagent": (
        "Agente que genera un informe legible en Markdown a partir de un "
        "ProjectInventory, resumiendo lenguajes detectados, herramientas, estado del "
        "README y listando errores y advertencias de la auditoría."
    ),
    "reportagent_save": (
        "Construye el informe Markdown del proyecto y lo escribe en "
        "<output_dir>/report.md (por defecto outputs/). Crea el directorio si no "
        "existe. Devuelve la ruta del fichero generado."
    ),
    # --- tools_agent.py ---
    "toolsagent": (
        "Agente que detecta herramientas de desarrollo (Docker, Docker Compose, Make, "
        "GitHub Actions, GitLab CI, Jupyter) y frameworks (FastAPI, Flask, Django, "
        "React, Vue, Angular, Express, Vite) presentes en un proyecto analizando sus "
        "ficheros de configuración y manifiestos de dependencias."
    ),
    "toolsagent_detect": (
        "Analiza los ficheros del proyecto (Dockerfile, Makefile, .github/workflows/, "
        "requirements.txt, pyproject.toml, package.json) y devuelve dos listas "
        "ordenadas: herramientas de infraestructura detectadas y frameworks detectados."
    ),
    # --- utils.py ---
    "githubcloneerror": (
        "Excepción personalizada (hereda de RuntimeError) que se lanza cuando falla "
        "la validación o la clonación de un repositorio de GitHub (URL inválida, git "
        "no instalado o fallo de red)."
    ),
    "is_github_url": (
        "Comprueba si una cadena de texto es una URL HTTPS válida de GitHub "
        "(esquema https y host exactamente github.com). Devuelve True o False."
    ),
    "clone_github_repo": (
        "Clona un repositorio de GitHub con git clone --depth 1 en un directorio "
        "temporal creado con tempfile. Devuelve la ruta local del repositorio clonado "
        "y su nombre. Lanza GitHubCloneError si la URL no es válida, git no está "
        "instalado o la clonación falla; limpia el directorio temporal en caso de error."
    ),
    "remove_temporary_directory": (
        "Elimina de forma segura un directorio temporal (creado por clone_github_repo) "
        "usando shutil.rmtree con ignore_errors=True. Es un no-op si la ruta es None "
        "o ya no existe."
    ),
    # --- main.py ---
    "build_parser": (
        "Construye y devuelve el parser CLI de la herramienta ci2-lab con el "
        "subcomando scan, que acepta una ruta de directorio local o una URL de "
        "GitHub como argumento posicional."
    ),
    "main_1": (
        "Punto de entrada CLI de ci2-lab. Parsea los argumentos, clona el repositorio "
        "si el input es una URL de GitHub (limpiando el directorio temporal al salir), "
        "ejecuta AuditorAgent.scan y devuelve código 0 si el inventario es válido o 1 "
        "si hay errores."
    ),
    # --- inventory_phase1.py ---
    "toolcandidate": (
        "Dataclass que representa un candidato a herramienta reutilizable detectado en "
        "un proyecto: identificador slug, nombre legible, proyecto de origen, rutas "
        "fuente, lista de evidencias encontradas, descripción breve, nivel de confianza "
        "(medium/high) y estado del registro."
    ),
    "slugify": (
        "Convierte una cadena arbitraria en un slug válido para usar como identificador "
        "de herramienta: pasa a minúsculas, sustituye caracteres no alfanuméricos por "
        "guiones bajos y elimina guiones bajos iniciales/finales."
    ),
    "now_iso": (
        "Devuelve la fecha y hora actual en formato ISO 8601 UTC sin microsegundos "
        "(p.ej. '2025-06-04T10:30:00+00:00'), para usar como timestamp en los "
        "manifiestos tool.yaml generados."
    ),
    "ensure_structure": (
        "Crea la estructura de directorios necesaria para el inventario si no existe: "
        "projects/raw, inventory/tools, inventory/capabilities, inventory/index, "
        "inventory/audit y agents."
    ),
    "detect_projects": (
        "Devuelve la lista de directorios de proyectos a analizar: si se pasa un "
        "argumento concreto resuelve esa ruta y la devuelve; si no, devuelve todos los "
        "subdirectorios de projects/raw/ ordenados alfabéticamente."
    ),
    "iter_project_files": (
        "Generador que recorre recursivamente todos los ficheros de un directorio de "
        "proyecto usando rglob, excluyendo cualquier ruta que contenga el directorio "
        ".git."
    ),
    "collect_signals": (
        "Recorre los ficheros de un proyecto y recoge evidencias de que es una "
        "herramienta reutilizable: detecta entrypoints conocidos (main.py, train.py, "
        "etc.), ficheros de dependencias, carpetas especiales (docs/, tests/, etc.), "
        "scripts SLURM (.sbatch) y notebooks. Devuelve dos listas: rutas fuente y "
        "textos de evidencia."
    ),
    "infer_name": (
        "Infiere el nombre legible de una herramienta a partir de sus rutas fuente: "
        "prioriza el nombre del fichero de entrada principal (main.py, train.py, etc.) "
        "y si no lo encuentra, usa el nombre del directorio del proyecto, convirtiendo "
        "guiones y guiones bajos en espacios y aplicando Title Case."
    ),
    "detect_candidate": (
        "Orquesta la detección completa de un candidato a herramienta: recoge "
        "evidencias con collect_signals, calcula la confianza (medium si <5 evidencias, "
        "high si ≥5) y construye un ToolCandidate. Devuelve None si hay menos de 2 "
        "evidencias (proyecto insuficiente)."
    ),
    "render_tool_yaml": (
        "Genera el contenido del fichero tool.yaml para un ToolCandidate, con todos "
        "los campos del manifiesto estándar: id, nombre, descripción, proyecto origen, "
        "rutas fuente, categoría, capacidades con evidencias, lenguajes, dependencias, "
        "modo de ejecución, entradas/salidas y metadatos de auditoría."
    ),
    "render_tool_readme": (
        "Genera el contenido del fichero README.md de un ToolCandidate con secciones "
        "estándar: descripción, capacidades, entradas, salidas, dependencias, modo de "
        "ejecución, ejemplo de uso, evidencias usadas y estado de documentación. Los "
        "campos sin información se marcan como pendientes."
    ),
    "write_tool": (
        "Escribe en disco la estructura completa de un tool detectado: crea el "
        "directorio inventory/tools/<tool_id>/ con subdirectorios source/, docs/, "
        "examples/ y tests/, y escribe los ficheros tool.yaml, README.md y un "
        "marcador SOURCE_PROJECT.txt. Devuelve el entry dict para el índice global."
    ),
    "write_tools_index": (
        "Escribe el fichero inventory/index/tools_index.json con la lista completa de "
        "tools detectados en la ejecución actual, serializada como JSON con "
        "indentación de 2 espacios."
    ),
    "main": (
        "Punto de entrada CLI del inventariador Phase 1. Parsea --project (proyecto "
        "concreto) y --clean (borrar tools previos), asegura la estructura de "
        "directorios, detecta proyectos, genera un ToolCandidate por cada uno y "
        "escribe los manifiestos y el índice global."
    ),
}


def patch() -> None:
    updated = 0
    not_found = []

    for slug, descripcion in DESCRIPCIONES.items():
        ficha_path = FICHAS_DIR / f"{slug}.json"
        if not ficha_path.exists():
            not_found.append(slug)
            continue

        data = json.loads(ficha_path.read_text(encoding="utf-8"))
        data["que_hace"] = descripcion
        ficha_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        updated += 1
        print(f"  [OK] {slug}.json")

    print(f"\nActualizadas: {updated} fichas.")
    if not_found:
        print(f"No encontradas: {not_found}")


if __name__ == "__main__":
    patch()
