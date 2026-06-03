# Arquitectura de Subagentes — CI2 Lab

## Objetivo del sistema

El objetivo de esta parte del proyecto **CI2 Lab** es construir un sistema basado en subagentes capaz de analizar repositorios de software de la Cátedra, extraer las herramientas utilizadas, documentarlas y generar un inventario técnico estructurado.

El sistema debe funcionar de forma modular. Cada subagente tendrá una responsabilidad concreta y el **Agente Auditor** será el encargado de coordinar el flujo general, supervisar los resultados y comprobar que todos los subagentes funcionan correctamente.

---

## Idea principal

El sistema no debe empezar como un agente complejo con muchas capacidades mezcladas.

Debe organizarse como un conjunto de subagentes especializados:

```text
Agente Auditor
    ├── Subagente Scanner
    ├── Subagente Detector de Lenguajes
    ├── Subagente Detector de Dependencias
    ├── Subagente Detector de Herramientas
    ├── Subagente Detector de Scripts
    ├── Subagente Detector de Documentación
    ├── Subagente Generador de Inventario
    └── Subagente Generador de Informe
```

El **Agente Auditor** actúa como controlador principal.
Los demás subagentes realizan tareas específicas y devuelven resultados estructurados.

---

## Arquitectura general

```text
Usuario
  |
  v
CLI / Entrada del sistema
  |
  v
Agente Auditor
  |
  ├── Subagente Scanner
  |
  ├── Subagente Detector de Lenguajes
  |
  ├── Subagente Detector de Dependencias
  |
  ├── Subagente Detector de Herramientas
  |
  ├── Subagente Detector de Scripts
  |
  ├── Subagente Detector de Documentación
  |
  ├── Subagente Generador de Inventario
  |
  └── Subagente Generador de Informe
  |
  v
Salidas finales
  |
  ├── inventory.json
  └── report.md
```

---

## Principio de diseño

El principio central del sistema es:

```text
Cada subagente hace una sola cosa y la hace bien.
El Agente Auditor coordina, valida y supervisa.
```

Esto permite que el sistema sea:

* más fácil de entender;
* más fácil de probar;
* más fácil de ampliar;
* más robusto ante errores;
* más adecuado para integrarse después con Claude Code.

---

# 1. Agente Auditor

## Rol principal

El **Agente Auditor** es el agente principal del sistema.

Su función no es detectar directamente herramientas ni analizar todos los archivos por sí mismo. Su función es coordinar a los subagentes, recibir sus resultados, validarlos y comprobar que el análisis final sea coherente.

El Agente Auditor es el responsable de decidir si el resultado final puede exportarse o si hay errores que deben corregirse.

---

## Responsabilidades del Agente Auditor

El Agente Auditor debe:

1. Recibir la ruta del repositorio.
2. Validar que la ruta existe.
3. Lanzar el Subagente Scanner.
4. Recibir la lista de archivos relevantes.
5. Llamar a los subagentes especializados.
6. Recoger los resultados de cada subagente.
7. Comprobar que los resultados no se contradicen.
8. Corregir errores simples y seguros.
9. Generar advertencias cuando falte información.
10. Validar que el inventario final tiene una estructura correcta.
11. Llamar al Subagente Generador de Inventario.
12. Llamar al Subagente Generador de Informe.
13. Mostrar un resumen final al usuario.

---

## Flujo del Agente Auditor

```text
1. Recibe la ruta del repositorio.
2. Comprueba que existe.
3. Llama al Subagente Scanner.
4. Recibe los archivos encontrados.
5. Llama al resto de subagentes.
6. Recibe resultados parciales.
7. Une todos los resultados.
8. Audita la coherencia del resultado.
9. Genera advertencias o errores.
10. Si todo es válido, genera las salidas finales.
```

---

## Validaciones del Agente Auditor

El Agente Auditor debe comprobar, como mínimo:

### Validaciones generales

* El nombre del proyecto existe.
* La ruta del proyecto existe.
* El inventario es serializable a JSON.
* Las listas no tienen duplicados.
* Las rutas son relativas cuando sea posible.
* Los campos obligatorios no están vacíos.
* Los resultados tienen tipos de datos correctos.

### Validaciones de coherencia

* Si existe `requirements.txt`, debe aparecer Python como lenguaje.
* Si existe `package.json`, debe aparecer Node.js como tecnología.
* Si existe `Dockerfile`, debe aparecer Docker como herramienta.
* Si existe `README.md`, documentación debe marcar `has_readme = true`.
* Si no existe `README.md`, documentación debe marcar `has_readme = false`.
* Si hay scripts `.sh`, Bash debe aparecer como lenguaje o tecnología auxiliar.
* Si hay `pyproject.toml`, debe detectarse un proyecto Python.
* Si hay `environment.yml`, debe detectarse Conda.
* Si hay `.ipynb`, debe detectarse Jupyter Notebook.

---

## Errores y advertencias

El Agente Auditor debe distinguir entre **errores** y **advertencias**.

### Errores

Un error impide generar una salida fiable.

Ejemplos:

```text
La ruta del repositorio no existe.
El inventario no se puede serializar a JSON.
Falta el nombre del proyecto.
El campo dependencies tiene un formato incorrecto.
El campo tools tiene un formato incorrecto.
```

### Advertencias

Una advertencia no impide generar la salida, pero indica que algo puede mejorarse o revisarse.

Ejemplos:

```text
README.md encontrado, pero no contiene sección de instalación.
requirements.txt encontrado, pero no se han extraído dependencias.
Dockerfile encontrado, pero no se ha detectado imagen base.
package.json encontrado, pero no contiene scripts.
Hay scripts de ejecución, pero no están documentados en el README.
```

---

## Salida del Agente Auditor

El Agente Auditor debe producir una estructura como esta:

```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    "README.md encontrado, pero no contiene sección de instalación.",
    "Dockerfile encontrado, pero no se ha detectado sección Docker en la documentación."
  ],
  "fixed_fields": [
    "languages",
    "tools"
  ]
}
```

---

# 2. Subagente Scanner

## Rol principal

El **Subagente Scanner** se encarga de recorrer el repositorio y encontrar archivos relevantes.

No debe analizar el significado de los archivos. Solo debe localizar, clasificar y devolver rutas.

---

## Responsabilidades

El Subagente Scanner debe:

* recorrer la carpeta del proyecto;
* ignorar carpetas innecesarias;
* detectar archivos relevantes;
* clasificar archivos por tipo;
* devolver rutas relativas;
* no ejecutar ningún archivo.

---

## Carpetas ignoradas

Debe ignorar:

```text
.git/
.venv/
venv/
__pycache__/
node_modules/
dist/
build/
.cache/
.ipynb_checkpoints/
.idea/
.vscode/
```

---

## Archivos relevantes

Debe buscar:

```text
requirements.txt
pyproject.toml
setup.py
setup.cfg
environment.yml
Pipfile
poetry.lock
package.json
package-lock.json
yarn.lock
pnpm-lock.yaml
Dockerfile
docker-compose.yml
docker-compose.yaml
Makefile
README.md
README.rst
docs/
*.sh
*.py
*.ipynb
*.yml
*.yaml
```

---

## Salida esperada

```json
{
  "project_path": "./repo_prueba",
  "project_name": "repo_prueba",
  "files": {
    "python": ["main.py", "src/utils.py"],
    "dependencies": ["requirements.txt", "pyproject.toml"],
    "node": ["package.json"],
    "docker": ["Dockerfile", "docker-compose.yml"],
    "scripts": ["run.sh", "install.sh"],
    "documentation": ["README.md", "docs/index.md"],
    "config": [".github/workflows/test.yml"]
  }
}
```

---

# 3. Subagente Detector de Lenguajes

## Rol principal

El **Subagente Detector de Lenguajes** identifica los lenguajes de programación utilizados en el repositorio.

---

## Responsabilidades

Debe detectar lenguajes a partir de extensiones y archivos característicos.

Ejemplos:

```text
.py       -> Python
.ipynb    -> Jupyter Notebook
.js       -> JavaScript
.ts       -> TypeScript
.sh       -> Bash
.java     -> Java
.cpp      -> C++
.c        -> C
.R        -> R
```

---

## Salida esperada

```json
{
  "languages": [
    "Python",
    "Bash",
    "Jupyter Notebook"
  ]
}
```

---

# 4. Subagente Detector de Dependencias

## Rol principal

El **Subagente Detector de Dependencias** extrae dependencias y gestores de paquetes.

---

## Archivos que analiza

```text
requirements.txt
pyproject.toml
setup.py
setup.cfg
environment.yml
Pipfile
package.json
```

---

## Responsabilidades

Debe detectar:

* dependencias de Python;
* dependencias de Node.js;
* dependencias de sistema cuando sea posible;
* gestores de paquetes;
* versiones si aparecen explícitamente.

---

## Gestores de paquetes detectables

```text
pip
conda
poetry
setuptools
npm
yarn
pnpm
```

---

## Salida esperada

```json
{
  "package_managers": ["pip", "conda"],
  "dependencies": {
    "python": ["numpy", "pandas", "scikit-learn"],
    "node": [],
    "system": []
  }
}
```

---

# 5. Subagente Detector de Herramientas

## Rol principal

El **Subagente Detector de Herramientas** identifica herramientas software, frameworks y utilidades de desarrollo.

---

## Herramientas iniciales

Debe detectar, como mínimo:

```text
Docker
Docker Compose
pytest
ruff
black
mypy
Jupyter
FastAPI
Flask
Django
React
Vue
Angular
Vite
Express
GitHub Actions
GitLab CI
Make
```

---

## Archivos que analiza

```text
Dockerfile
docker-compose.yml
docker-compose.yaml
pyproject.toml
requirements.txt
package.json
Makefile
.github/workflows/*
.gitlab-ci.yml
```

---

## Salida esperada

```json
{
  "tools": [
    "Docker",
    "pytest",
    "ruff",
    "Jupyter"
  ],
  "frameworks": [
    "FastAPI"
  ],
  "ci_tools": [
    "GitHub Actions"
  ]
}
```

---

# 6. Subagente Detector de Scripts

## Rol principal

El **Subagente Detector de Scripts** identifica scripts de ejecución, instalación, pruebas o automatización.

---

## Archivos que analiza

```text
*.sh
Makefile
package.json
pyproject.toml
```

---

## Responsabilidades

Debe detectar comandos como:

```text
python main.py
python train.py
pytest
make run
make test
docker build
docker compose up
npm run dev
npm test
```

---

## Clasificación de scripts

Los scripts pueden clasificarse como:

```text
installation
execution
testing
build
deployment
utility
unknown
```

---

## Salida esperada

```json
{
  "scripts": [
    {
      "path": "run.sh",
      "type": "execution",
      "commands": ["python main.py"]
    },
    {
      "path": "Makefile",
      "type": "testing",
      "commands": ["pytest"]
    }
  ]
}
```

---

# 7. Subagente Detector de Documentación

## Rol principal

El **Subagente Detector de Documentación** comprueba la documentación existente.

No debe inventar documentación. Solo debe analizar lo que existe.

---

## Archivos que analiza

```text
README.md
README.rst
docs/
INSTALL.md
CONTRIBUTING.md
CHANGELOG.md
```

---

## Responsabilidades

Debe detectar:

* si existe README;
* si existe carpeta `docs/`;
* si hay sección de instalación;
* si hay sección de uso;
* si hay sección de ejemplos;
* si hay sección de tests;
* si hay sección de Docker;
* si hay sección de arquitectura;
* si hay sección de dependencias;
* qué secciones faltan.

---

## Secciones buscadas

```text
Installation
Instalación
Usage
Uso
Requirements
Requisitos
Dependencies
Dependencias
Examples
Ejemplos
Execution
Ejecución
Tests
Pruebas
Docker
Architecture
Arquitectura
```

---

## Salida esperada

```json
{
  "documentation": {
    "has_readme": true,
    "has_docs_folder": false,
    "has_installation_section": true,
    "has_usage_section": true,
    "has_examples_section": false,
    "has_tests_section": false,
    "has_docker_section": false,
    "has_architecture_section": false,
    "missing_sections": [
      "examples",
      "tests",
      "docker"
    ]
  }
}
```

---

# 8. Subagente Generador de Inventario

## Rol principal

El **Subagente Generador de Inventario** construye el archivo estructurado final `inventory.json`.

No analiza archivos directamente. Solo recibe los resultados validados por el Agente Auditor y los transforma en JSON.

---

## Responsabilidades

Debe:

* crear una estructura JSON clara;
* incluir los resultados de todos los subagentes;
* ordenar listas;
* eliminar duplicados;
* incluir advertencias del Agente Auditor;
* guardar el archivo en `outputs/inventory.json`.

---

## Formato esperado

```json
{
  "project_name": "repo_prueba",
  "project_path": "./repo_prueba",
  "languages": ["Python", "Bash"],
  "package_managers": ["pip"],
  "dependencies": {
    "python": ["numpy", "pandas"],
    "node": [],
    "system": []
  },
  "tools": ["Docker", "pytest"],
  "frameworks": [],
  "scripts": [
    {
      "path": "run.sh",
      "type": "execution",
      "commands": ["python main.py"]
    }
  ],
  "documentation": {
    "has_readme": true,
    "has_installation_section": false,
    "has_usage_section": true
  },
  "audit": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  }
}
```

---

# 9. Subagente Generador de Informe

## Rol principal

El **Subagente Generador de Informe** genera un informe legible en Markdown.

No debe modificar el inventario. Solo debe convertirlo en un documento fácil de leer.

---

## Responsabilidades

Debe generar:

```text
outputs/report.md
```

El informe debe incluir:

* resumen del proyecto;
* lenguajes detectados;
* dependencias detectadas;
* herramientas detectadas;
* scripts relevantes;
* estado de la documentación;
* advertencias del Agente Auditor;
* recomendaciones básicas.

---

## Estructura esperada del informe

```markdown
# Informe de inventario: repo_prueba

## Resumen

El proyecto analizado utiliza Python y Bash. Se han detectado dependencias gestionadas mediante pip y varios scripts de ejecución.

## Lenguajes detectados

- Python
- Bash

## Dependencias

### Python

- numpy
- pandas

## Herramientas detectadas

- Docker
- pytest

## Scripts detectados

- run.sh: script de ejecución

## Estado de la documentación

- README encontrado.
- Sección de instalación no encontrada.
- Sección de uso encontrada.

## Auditoría

### Advertencias

- README.md encontrado, pero no contiene sección de instalación.

## Recomendaciones

- Añadir instrucciones de instalación.
- Documentar cómo ejecutar el proyecto.
```

---

# 10. Soporte para URLs de GitHub

## Objetivo

Permitir que el sistema acepte directamente una URL de un repositorio de GitHub como entrada, sin que el usuario tenga que clonarlo manualmente.

---

## Comportamiento esperado

Cuando el usuario pase una URL de GitHub en lugar de una ruta local, el sistema debe:

1. Detectar que la entrada es una URL y no una ruta local.
2. Clonar el repositorio en una carpeta temporal.
3. Ejecutar el análisis sobre esa carpeta temporal exactamente igual que si fuera una ruta local.
4. Eliminar la carpeta temporal al finalizar el análisis.
5. Guardar los resultados en `outputs/` como siempre.

---

## Comando esperado

```bash
python -m ci2_lab.main scan https://github.com/usuario/repositorio
```

El comportamiento desde el punto de vista del usuario debe ser idéntico al de una ruta local. La diferencia es interna.

---

## Responsabilidades

Esta funcionalidad debe implementarse como un paso previo al Agente Auditor, dentro de `main.py`.

El módulo principal debe:

* detectar si el argumento de entrada comienza por `https://github.com`;
* si es una URL, delegar en un módulo auxiliar `utils.py` que gestione la clonación;
* pasar al Agente Auditor la ruta temporal resultante, igual que si fuera una ruta local;
* garantizar que la carpeta temporal se elimina siempre al finalizar, incluso si ocurre un error.

El Agente Auditor y el resto de subagentes **no deben saber** si el origen era una URL o una ruta local. Reciben siempre una ruta local válida.

---

## Módulo auxiliar recomendado

La lógica de clonación debe vivir en `utils.py` como una función independiente:

```python
def clone_github_repo(url: str) -> str:
    """
    Clona un repositorio de GitHub en una carpeta temporal.
    Devuelve la ruta local de la carpeta temporal.
    """
```

La gestión de la carpeta temporal debe usar `tempfile.mkdtemp()` de la librería estándar de Python.

La clonación debe hacerse con `git clone` mediante `subprocess`, sin instalar dependencias adicionales.

---

## Gestión de errores

Deben contemplarse los siguientes casos de error:

```text
La URL no es un repositorio de GitHub válido.
El repositorio no existe o es privado.
Git no está instalado en el sistema.
No hay conexión a internet.
La clonación falla por cualquier otro motivo.
```

En todos estos casos, el sistema debe mostrar un mensaje de error claro y detener la ejecución sin generar archivos de salida parciales.

---

## Limpieza de la carpeta temporal

La carpeta temporal debe eliminarse siempre al finalizar, tanto si el análisis fue exitoso como si ocurrió un error. Debe usarse un bloque `try/finally` para garantizarlo:

```python
try:
    ruta_local = clone_github_repo(url)
    auditor.scan(ruta_local)
finally:
    eliminar_carpeta_temporal(ruta_local)
```

---

## Salida esperada en consola

```text
Clonando repositorio: https://github.com/usuario/repositorio
Repositorio clonado correctamente.

Analizando proyecto: repositorio

[1/8] Scanner ejecutado correctamente.
...
[8/8] Informes generados.

Resultado:
- outputs/inventory.json
- outputs/report.md

Limpiando carpeta temporal...
Listo.
```

---

## Reglas importantes

* El sistema **nunca debe ejecutar** ningún archivo del repositorio clonado, igual que con los repositorios locales.
* La clonación debe ser **superficial** (`git clone --depth 1`) para reducir tiempo y espacio en disco.
* El nombre del proyecto en el inventario debe extraerse del nombre del repositorio en la URL, no de la ruta temporal.

---

## Cambios necesarios en el código

Los únicos archivos que requieren modificación o creación son:

```text
src/ci2_lab/main.py        — detectar si la entrada es URL y coordinar la limpieza
src/ci2_lab/utils.py       — añadir función clone_github_repo y eliminar_carpeta_temporal
tests/test_github_input.py — tests para URLs válidas, inválidas y errores de red
```

El resto del sistema no necesita ningún cambio.

---

# Flujo completo del sistema

```text
1. El usuario ejecuta el análisis sobre un repositorio (ruta local o URL de GitHub).

2. Si la entrada es una URL de GitHub, main.py clona el repositorio en una carpeta temporal
   y pasa esa ruta al Agente Auditor.

3. El Agente Auditor recibe la ruta local.

4. El Agente Auditor valida la ruta.

5. El Agente Auditor llama al Subagente Scanner.

6. El Scanner devuelve los archivos relevantes.

7. El Agente Auditor llama a los subagentes especializados:
   - Detector de Lenguajes
   - Detector de Dependencias
   - Detector de Herramientas
   - Detector de Scripts
   - Detector de Documentación

8. Cada subagente devuelve su resultado parcial.

9. El Agente Auditor une los resultados.

10. El Agente Auditor valida la coherencia global.

11. Si hay errores graves, detiene la exportación.

12. Si solo hay advertencias, continúa.

13. El Agente Auditor llama al Generador de Inventario.

14. El Agente Auditor llama al Generador de Informe.

15. Se generan las salidas finales.

16. Si el origen era una URL, main.py elimina la carpeta temporal.
```

---

# Estructura recomendada del código

```text
ci2-lab-agent/
│
├── README.md
├── CLAUDE.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── src/
│   └── ci2_lab/
│       ├── __init__.py
│       ├── main.py
│       ├── models.py
│       ├── utils.py
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── auditor_agent.py
│       │   ├── scanner_agent.py
│       │   ├── language_agent.py
│       │   ├── dependency_agent.py
│       │   ├── tools_agent.py
│       │   ├── scripts_agent.py
│       │   ├── documentation_agent.py
│       │   ├── inventory_agent.py
│       │   └── report_agent.py
│       │
│       └── detectors/
│           ├── __init__.py
│           ├── python_detector.py
│           ├── node_detector.py
│           ├── docker_detector.py
│           ├── script_detector.py
│           └── docs_detector.py
│
├── outputs/
│   ├── inventory.json
│   └── report.md
│
├── examples/
│   └── repo_prueba/
│
└── tests/
    ├── test_auditor_agent.py
    ├── test_scanner_agent.py
    ├── test_language_agent.py
    ├── test_dependency_agent.py
    ├── test_tools_agent.py
    ├── test_scripts_agent.py
    ├── test_documentation_agent.py
    └── test_github_input.py
```

---

# Diferencia entre agentes y detectores

Es importante mantener esta separación:

```text
agents/    -> coordinan tareas y devuelven resultados de alto nivel.
detectors/ -> contienen reglas concretas para detectar patrones.
```

Ejemplo:

```text
dependency_agent.py
    usa:
        python_detector.py
        node_detector.py

tools_agent.py
    usa:
        docker_detector.py
        docs_detector.py

documentation_agent.py
    usa:
        docs_detector.py
```

Los agentes organizan el trabajo.
Los detectores hacen búsquedas concretas.

---

# Modelos de datos recomendados

## Resultado del Scanner

```python
from dataclasses import dataclass, field


@dataclass
class ScanResult:
    project_name: str
    project_path: str
    files: dict[str, list[str]] = field(default_factory=dict)
```

---

## Resultado de Auditoría

```python
from dataclasses import dataclass, field


@dataclass
class AuditResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixed_fields: list[str] = field(default_factory=list)
```

---

## Inventario del proyecto

```python
from dataclasses import dataclass, field


@dataclass
class ProjectInventory:
    project_name: str
    project_path: str
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    scripts: list[dict] = field(default_factory=list)
    documentation: dict = field(default_factory=dict)
    audit: dict = field(default_factory=dict)
```

---

# Comando esperado

El comando principal puede recibir una ruta local o una URL de GitHub:

```bash
python -m ci2_lab.main scan ./examples/repo_prueba
python -m ci2_lab.main scan https://github.com/usuario/repositorio
```

Más adelante, si se configura como CLI instalable:

```bash
ci2-lab scan ./examples/repo_prueba
ci2-lab scan https://github.com/usuario/repositorio
```

---

# Ejemplo de ejecución esperada

Con ruta local:

```text
Analizando proyecto: repo_prueba

[1/8] Scanner ejecutado correctamente.
[2/8] Lenguajes detectados.
[3/8] Dependencias detectadas.
[4/8] Herramientas detectadas.
[5/8] Scripts detectados.
[6/8] Documentación analizada.
[7/8] Auditoría completada.
[8/8] Informes generados.

Resultado:
- outputs/inventory.json
- outputs/report.md

Advertencias:
- README.md encontrado, pero no contiene sección de instalación.
```

Con URL de GitHub:

```text
Clonando repositorio: https://github.com/usuario/repositorio
Repositorio clonado correctamente.

Analizando proyecto: repositorio

[1/8] Scanner ejecutado correctamente.
[2/8] Lenguajes detectados.
[3/8] Dependencias detectadas.
[4/8] Herramientas detectadas.
[5/8] Scripts detectados.
[6/8] Documentación analizada.
[7/8] Auditoría completada.
[8/8] Informes generados.

Resultado:
- outputs/inventory.json
- outputs/report.md

Limpiando carpeta temporal...
Listo.
```

---

# Reglas importantes

## Seguridad

El sistema nunca debe ejecutar código del repositorio analizado.

No debe ejecutar:

```bash
python script.py
bash run.sh
make run
docker build .
npm install
pip install
```

Solo debe leer archivos.

---

## Simplicidad

No añadir todavía:

```text
RAG
base de datos vectorial
interfaz web
multiagentes complejos
ejecución real en clúster
automatización HPC
```

La primera versión debe centrarse en:

```text
leer archivos
detectar tecnologías
generar inventario
generar informe
auditar coherencia
```

---

## Determinismo

Para que los resultados sean comparables entre ejecuciones:

* ordenar listas;
* eliminar duplicados;
* usar rutas relativas;
* evitar inferencias débiles;
* no inventar dependencias;
* no inventar herramientas;
* no inventar documentación.

---

# Prioridad de desarrollo

El orden recomendado es:

```text
1. Crear estructura del repositorio.
2. Implementar modelos de datos.
3. Implementar Subagente Scanner.
4. Implementar Agente Auditor básico.
5. Implementar Detector de Lenguajes.
6. Implementar Detector de Dependencias.
7. Implementar Detector de Herramientas.
8. Implementar Detector de Scripts.
9. Implementar Detector de Documentación.
10. Implementar Generador de Inventario.
11. Implementar Generador de Informe.
12. Implementar soporte para URLs de GitHub.
13. Añadir tests.
```

---

# Primera versión mínima

La primera versión mínima debe poder:

1. Recibir una ruta de repositorio local o una URL de GitHub.
2. Escanear archivos relevantes.
3. Detectar Python si existe `requirements.txt` o archivos `.py`.
4. Detectar Node.js si existe `package.json`.
5. Detectar Docker si existe `Dockerfile`.
6. Detectar README.
7. Generar `inventory.json`.
8. Generar `report.md`.
9. Incluir auditoría con errores y advertencias.
10. No ejecutar ningún archivo del proyecto analizado.
11. Limpiar carpetas temporales si el origen era una URL.

---

# Criterios de éxito

La arquitectura se considera correcta si:

* el Agente Auditor coordina todo el flujo;
* cada subagente tiene una responsabilidad única;
* los subagentes devuelven datos estructurados;
* el sistema genera un inventario legible;
* el sistema genera un informe en Markdown;
* la auditoría detecta incoherencias;
* ningún componente ejecuta código del repositorio analizado;
* el sistema acepta tanto rutas locales como URLs de GitHub;
* añadir un nuevo subagente no obliga a reescribir todo el sistema.

---

# Resumen final

El sistema CI2 Lab debe construirse como una arquitectura modular de subagentes.

El **Agente Auditor** será el núcleo del sistema:

```text
Coordina
Valida
Supervisa
Corrige incoherencias simples
Genera advertencias
Autoriza la exportación final
```

Los subagentes se encargan de tareas concretas:

```text
Scanner
Lenguajes
Dependencias
Herramientas
Scripts
Documentación
Inventario
Informe
```

La entrada puede ser una ruta local o una URL de GitHub. En ambos casos el flujo interno es idéntico: `main.py` se encarga de resolver la entrada a una ruta local antes de pasársela al Agente Auditor.

Esta estructura permite empezar con una versión simple, clara y mantenible, y evolucionar más adelante hacia un sistema más inteligente integrado con Claude Code.
