#!/usr/bin/env python3
"""
Genera fichas JSON para el catálogo CI2 a partir de un repositorio local.

Uso:
    python scripts/generate_fichas.py --repo <ruta_repo> --proyecto <nombre>

Por cada función/clase pública encontrada en ficheros .py genera una ficha JSON
en fichas/<proyecto>/<nombre>.json.  Las piezas descartadas (stubs, privadas, etc.)
se registran en fichas/<proyecto>/_omitidas.json para revisión humana.
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

CATALOG_ROOT = Path(__file__).parent.parent

# Directorios que se saltan siempre
SKIP_DIRS = {
    "__pycache__", ".venv", "venv", "env", ".git",
    "node_modules", "dist", "build", ".mypy_cache", ".pytest_cache",
    "catalogo",  # carpeta de salida del propio catálogo
}

# Funciones genéricas que no aportan valor como pieza reutilizable
OMIT_NAMES = {
    "__init__", "__str__", "__repr__", "__eq__", "__hash__",
    "__lt__", "__le__", "__gt__", "__ge__", "__len__", "__iter__",
    "__enter__", "__exit__", "__call__", "__contains__",
    "setup", "teardown", "setUp", "tearDown",
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "are", "has",
    "returns", "return", "param", "args", "kwargs", "self", "cls",
    "def", "class", "none", "true", "false", "str", "int", "list",
    "dict", "bool", "path", "file", "type", "object", "value", "error",
    "que", "una", "los", "las", "para", "con", "por", "del", "como",
    "cada", "cuando", "dado", "desde", "hasta", "sobre", "bajo",
}


# ---------------------------------------------------------------------------
# Utilidades git / proyecto
# ---------------------------------------------------------------------------

def git_last_author(repo: Path, filepath: Path) -> str:
    try:
        rel = str(filepath.relative_to(repo)).replace("\\", "/")
        result = subprocess.run(
            ["git", "--no-pager", "log", "--follow", "-1", "--format=%an", rel],
            cwd=str(repo), capture_output=True, text=True, timeout=10,
        )
        author = result.stdout.strip()
        return author if author else "por confirmar"
    except Exception:
        return "por confirmar"


def read_project_deps(repo: Path) -> list[str]:
    deps: list[str] = []

    req = repo / "requirements.txt"
    if req.exists():
        for line in req.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                pkg = re.split(r"[>=<!;\[]", line)[0].strip()
                if pkg:
                    deps.append(pkg)

    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if re.match(r'dependencies\s*=\s*\[', stripped):
                in_deps = True
                continue
            if in_deps:
                if stripped.startswith("]"):
                    break
                m = re.search(r'["\']([a-zA-Z0-9_\-]+)', stripped)
                if m:
                    deps.append(m.group(1))

    return sorted(set(deps))


def get_local_package_names(repo: Path) -> set[str]:
    """Detecta los nombres de paquetes locales del propio repo para excluirlos del stack."""
    names: set[str] = set()
    # Convención src/<package>/
    src = repo / "src"
    if src.is_dir():
        for child in src.iterdir():
            if child.is_dir() and (child / "__init__.py").exists():
                names.add(child.name)
    # Nombre del proyecto en pyproject.toml
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        m = re.search(r'name\s*=\s*["\']([a-zA-Z0-9_\-]+)["\']', content)
        if m:
            names.add(m.group(1).replace("-", "_"))
    return names


def get_python_version(repo: Path) -> str:
    pyproject = repo / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        m = re.search(r'python\s*=\s*["\']>=?\s*([\d.]+)', content)
        if m:
            return f">={m.group(1)}"
    return "3.x"


# ---------------------------------------------------------------------------
# Análisis AST
# ---------------------------------------------------------------------------

def get_file_imports(tree: ast.Module) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def format_args(args: ast.arguments) -> str:
    parts: list[str] = []
    all_args = args.args + args.kwonlyargs
    defaults = args.defaults
    offset = len(all_args) - len(defaults)

    for i, arg in enumerate(all_args):
        if arg.arg in ("self", "cls"):
            continue
        part = arg.arg
        if arg.annotation:
            try:
                part += f": {ast.unparse(arg.annotation)}"
            except Exception:
                pass
        if i >= offset:
            try:
                part += f" = {ast.unparse(defaults[i - offset])}"
            except Exception:
                pass
        parts.append(part)

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    return ", ".join(parts) if parts else "—"


def is_stub(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True si el cuerpo es solo pass / ... / docstring."""
    body = node.body
    if len(body) == 1:
        stmt = body[0]
        if isinstance(stmt, ast.Pass):
            return True
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            return True  # solo docstring o ellipsis
    if len(body) == 2:
        first, second = body
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(second, (ast.Pass, ast.Expr))):
            return True
    return False


def should_omit(name: str, docstring: Optional[str], node) -> tuple[bool, str]:
    if name in OMIT_NAMES:
        return True, f"método especial ({name})"
    if name.startswith("_"):
        return True, "símbolo privado"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_stub(node):
        return True, "stub sin implementación"
    return False, ""


def split_identifier(name: str) -> list[str]:
    """Divide un identificador CamelCase o snake_case en tokens."""
    # snake_case
    parts = [p for p in name.split("_") if p]
    # CamelCase dentro de cada parte
    tokens: list[str] = []
    for part in parts:
        sub = re.sub(r"([A-Z][a-z]+)", r" \1", part)
        sub = re.sub(r"([A-Z]+)(?=[A-Z][a-z])", r" \1", sub)
        tokens.extend(sub.lower().split())
    return tokens


def extract_etiquetas(name: str, docstring: str) -> list[str]:
    # Tokens del nombre del identificador (primera fuente)
    name_tokens = split_identifier(name)
    # Tokens del docstring
    doc_tokens = re.findall(r"[a-záéíóúñ]{4,}", (docstring or "").lower())
    all_tokens = name_tokens + doc_tokens

    seen: set[str] = set()
    tags: list[str] = []
    for token in all_tokens:
        clean = token.strip("_")
        if clean and len(clean) >= 3 and clean not in STOPWORDS and clean not in seen:
            tags.append(clean)
            seen.add(clean)
        if len(tags) == 5:
            break
    return tags


def build_stack(
    python_version: str,
    project_deps: list[str],
    file_imports: set[str],
    local_pkgs: set[str],
) -> str:
    stdlib_skip = {
        "os", "sys", "re", "json", "pathlib", "typing", "abc", "ast",
        "subprocess", "datetime", "collections", "itertools", "functools",
        "dataclasses", "enum", "math", "io", "time", "copy", "warnings",
        "hashlib", "uuid", "struct", "argparse", "logging", "__future__",
    }
    # Sólo deps externas realmente importadas
    used = [d for d in project_deps if d in file_imports and d not in local_pkgs]
    extra = [
        i for i in sorted(file_imports)
        if i not in stdlib_skip
        and i not in project_deps
        and i not in local_pkgs
        and not i.startswith("_")
        and len(i) > 1
    ]
    parts = [f"Python {python_version}"] + used + extra
    return ", ".join(parts[:6]) if len(parts) > 1 else parts[0]


# ---------------------------------------------------------------------------
# Generación de fichas
# ---------------------------------------------------------------------------

def ficha_from_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    filepath: Path,
    repo: Path,
    proyecto: str,
    project_deps: list[str],
    file_imports: set[str],
    author: str,
    python_version: str,
    local_pkgs: set[str],
    parent_class: Optional[str] = None,
) -> tuple[Optional[dict], Optional[dict]]:

    docstring = ast.get_docstring(node) or ""
    omit, reason = should_omit(node.name, docstring, node)
    rel = filepath.relative_to(repo)

    if omit:
        return None, {"nombre": node.name, "razon": reason,
                      "fichero": str(rel).replace("\\", "/")}

    ret = ""
    if node.returns:
        try:
            ret = ast.unparse(node.returns)
        except Exception:
            pass

    args_str = format_args(node.args)
    io = f"Entrada: ({args_str})"
    io += f" → {ret}" if ret else " → por confirmar"

    location = str(rel).replace("\\", "/")
    if parent_class:
        location += f" :: {parent_class}.{node.name}"
    else:
        location += f" :: {node.name}"

    return {
        "nombre": f"{parent_class}.{node.name}" if parent_class else node.name,
        "proyecto": proyecto,
        "que_hace": docstring if docstring else "por confirmar",
        "donde_vive": location,
        "stack": build_stack(python_version, project_deps, file_imports, local_pkgs),
        "entrada_salida": io,
        "mantiene": author,
        "etiquetas": extract_etiquetas(node.name, docstring),
    }, None


def ficha_from_class(
    node: ast.ClassDef,
    filepath: Path,
    repo: Path,
    proyecto: str,
    project_deps: list[str],
    file_imports: set[str],
    author: str,
    python_version: str,
    local_pkgs: set[str],
) -> tuple[Optional[dict], Optional[dict]]:

    docstring = ast.get_docstring(node) or ""
    omit, reason = should_omit(node.name, docstring, node)
    rel = filepath.relative_to(repo)

    if omit:
        return None, {"nombre": node.name, "razon": reason,
                      "fichero": str(rel).replace("\\", "/")}

    public_methods = [
        m.name for m in node.body
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not m.name.startswith("_")
    ]
    methods_str = ", ".join(public_methods) if public_methods else "—"

    decorators = [
        ast.unparse(d) for d in node.decorator_list
        if isinstance(d, ast.Name)
    ]
    is_dataclass = "dataclass" in decorators

    io = "Clase (dataclass)" if is_dataclass else f"Clase. Métodos públicos: {methods_str}"

    return {
        "nombre": node.name,
        "proyecto": proyecto,
        "que_hace": docstring if docstring else "por confirmar",
        "donde_vive": f"{str(rel).replace(chr(92), '/')} :: class {node.name}",
        "stack": build_stack(python_version, project_deps, file_imports, local_pkgs),
        "entrada_salida": io,
        "mantiene": author,
        "etiquetas": extract_etiquetas(node.name, docstring),
    }, None


def scan_python_file(
    filepath: Path,
    repo: Path,
    proyecto: str,
    project_deps: list[str],
    python_version: str,
    local_pkgs: set[str],
) -> tuple[list[dict], list[dict]]:

    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"  [WARN] No se pudo parsear {filepath.name}: {exc}", file=sys.stderr)
        return [], []

    file_imports = get_file_imports(tree)
    author = git_last_author(repo, filepath)

    fichas: list[dict] = []
    omitidas: list[dict] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            f, o = ficha_from_function(
                node, filepath, repo, proyecto,
                project_deps, file_imports, author, python_version, local_pkgs,
            )
            (fichas if f else omitidas).append(f or o)

        elif isinstance(node, ast.ClassDef):
            f, o = ficha_from_class(
                node, filepath, repo, proyecto,
                project_deps, file_imports, author, python_version, local_pkgs,
            )
            if f:
                fichas.append(f)
            else:
                omitidas.append(o)
                continue

            # Métodos públicos no-triviales de la clase como fichas individuales
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mf, mo = ficha_from_function(
                        child, filepath, repo, proyecto,
                        project_deps, file_imports, author, python_version, local_pkgs,
                        parent_class=node.name,
                    )
                    (fichas if mf else omitidas).append(mf or mo)

    return fichas, omitidas


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def generate(repo_path: str, proyecto: str) -> None:
    repo = Path(repo_path).resolve()
    if not repo.exists():
        print(f"ERROR: no existe el path '{repo}'", file=sys.stderr)
        sys.exit(1)

    out_dir = CATALOG_ROOT / "fichas" / proyecto
    out_dir.mkdir(parents=True, exist_ok=True)

    project_deps = read_project_deps(repo)
    python_version = get_python_version(repo)
    local_pkgs = get_local_package_names(repo)

    print(f"Repo    : {repo}")
    print(f"Proyecto: {proyecto}")
    print(f"Deps    : {', '.join(project_deps) if project_deps else '—'}")
    print(f"Python  : {python_version}")
    print(f"Pkgs loc: {', '.join(local_pkgs) if local_pkgs else '—'}")
    print()

    all_fichas: list[dict] = []
    all_omitidas: list[dict] = []

    for py_file in sorted(repo.rglob("*.py")):
        if any(part in SKIP_DIRS for part in py_file.parts):
            continue
        fichas, omitidas = scan_python_file(
            py_file, repo, proyecto, project_deps, python_version, local_pkgs
        )
        all_fichas.extend(fichas)
        all_omitidas.extend(omitidas)

    # Escribir fichas
    written = 0
    slugs_seen: dict[str, int] = {}
    for ficha in all_fichas:
        base = re.sub(r"[^a-zA-Z0-9_]", "_", ficha["nombre"]).lower()
        # Evitar colisiones de nombre
        count = slugs_seen.get(base, 0)
        slug = base if count == 0 else f"{base}_{count}"
        slugs_seen[base] = count + 1

        (out_dir / f"{slug}.json").write_text(
            json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  [OK]  {slug}.json  —  {ficha['donde_vive']}")
        written += 1

    # Escribir auditoría de omitidas
    if all_omitidas:
        audit = out_dir / "_omitidas.json"
        audit.write_text(
            json.dumps(all_omitidas, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print()
    print(f"Fichas generadas : {written}")
    print(f"Piezas omitidas  : {len(all_omitidas)}  →  fichas/{proyecto}/_omitidas.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera fichas JSON para el catálogo CI2"
    )
    parser.add_argument("--repo", required=True, help="Ruta al repositorio a analizar")
    parser.add_argument(
        "--proyecto", required=True, help="Nombre del proyecto (slug, sin espacios)"
    )
    args = parser.parse_args()
    generate(args.repo, args.proyecto)
