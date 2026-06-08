# Informe Resumido: Estado de los agentes

## 1. Objetivo del proyecto

Construir un sistema de agentes capaz de:

- analizar repositorios de software sin ejecutar codigo
- detectar tecnologias, dependencias, scripts y documentacion
- generar un inventario tecnico estructurado
- evolucionar despues hacia un inventario de herramientas reutilizables y capacidades del laboratorio

## 2. Idea principal

El sistema esta organizado como una arquitectura de agentes especializados.

Esquema general:

```text
Entrada del usuario
    ->
Agente Auditor
    ->
Scanner + Lenguajes + Dependencias + Herramientas + Scripts + Documentacion
    ->
Inventario JSON + Informe Markdown
```

La idea es simple:

- cada agente hace una tarea concreta
- el Agente Auditor coordina todo
- el sistema no ejecuta codigo del repositorio analizado

## 3. Que hace cada agente

### `AuditorAgent`

Es el agente principal.

Se encarga de:

- recibir la ruta local o URL de GitHub
- coordinar a los demas agentes
- unir todos los resultados
- hacer comprobaciones basicas de coherencia
- generar las salidas finales

### `ScannerAgent`

Se encarga de recorrer el repositorio y clasificar archivos relevantes.

Detecta, por ejemplo:

- Python
- dependencias
- Docker
- scripts
- documentacion
- notebooks
- CI/CD

### `LanguageAgent`

Detecta los lenguajes usados en el proyecto.

Actualmente reconoce:

- Python
- Bash
- Node.js
- Jupyter Notebook
- YAML

### `DependencyAgent`

Lee los archivos de dependencias y detecta:

- gestores de paquetes
- librerias Python
- dependencias Node

Archivos soportados:

- `requirements.txt`
- `pyproject.toml`
- `environment.yml`
- `Pipfile`
- `poetry.lock`
- `package.json`
- `yarn.lock`
- `pnpm-lock.yaml`

### `ToolsAgent`

Detecta herramientas y frameworks del proyecto.

Ejemplos que ya reconoce:

- Docker
- Docker Compose
- Make
- GitHub Actions
- GitLab CI
- pytest
- ruff
- black
- FastAPI
- Flask
- Django
- React
- Vue
- Angular
- Vite
- Express

### `ScriptsAgent`

Analiza scripts y extrae comandos basicos.

Actualmente soporta:

- `.sh`
- `Makefile`

### `DocumentationAgent`

Analiza la documentacion del repositorio.

Comprueba:

- si existe README
- si existe carpeta `docs/`
- si hay secciones de instalacion, uso, ejemplos, tests, Docker, arquitectura y dependencias

### `InventoryAgent`

Genera el archivo:

- `outputs/inventory.json`

### `ReportAgent`

Genera el archivo:

- `outputs/report.md`

## 4. Flujo actual del sistema

```text
1. El usuario lanza el analisis
2. Si la entrada es GitHub, se clona el repo en temporal
3. ScannerAgent clasifica archivos
4. Los agentes especializados analizan el proyecto
5. AuditorAgent valida y consolida resultados
6. Se generan inventory.json y report.md
7. Si venia de GitHub, se elimina la carpeta temporal
```

## 5. Que esta ya hecho

Actualmente ya funciona:

- CLI con comando `scan`
- analisis de rutas locales
- analisis de URLs publicas de GitHub
- clonacion superficial con limpieza de temporales
- escaneo de archivos relevantes
- deteccion de lenguajes
- deteccion de dependencias
- deteccion de herramientas y frameworks
- analisis basico de scripts
- analisis basico de documentacion
- generacion de `inventory.json`
- generacion de `report.md`
- tests automatizados para estas partes

## 6. Que llevamos avanzado pero aun basico

- la auditoria existe, pero todavia es basica
- el analisis de scripts funciona, pero con heuristicas simples
- la clasificacion de lenguajes y herramientas es correcta, pero todavia ampliable
- ya existe una primera estructura para inventariar herramientas reutilizables

## 7. Segunda linea del proyecto: inventario de herramientas y capacidades

Ademas del analisis tecnico del repositorio, ya hemos empezado una segunda capa del proyecto.

Su objetivo es:

- detectar herramientas reutilizables dentro de proyectos
- documentarlas
- clasificarlas por capacidades
- construir un catalogo reutilizable para futuros proyectos

Elementos ya preparados:

- documentos de arquitectura en `agents/`
- taxonomia de capacidades en `inventory/capabilities/capabilities.yaml`
- script inicial de inventario en `scripts/inventory_phase1.py`
- catalogo de fichas en `catalogo/`

## 8. Agentes planteados para esa segunda fase

Ya estan definidos a nivel de diseño:

- `ToolInventoryMainAgent`: coordinador del inventario completo
- `ToolExtractionAgent`: detecta herramientas candidatas
- `DependencyAgent` ampliado: detecta requisitos mas avanzados
- `DocumentationAgent` ampliado: resume documentacion por herramienta
- `CapabilityClassifierAgent`: clasifica por capacidades
- `RecommendationAgent`: recomienda herramientas para nuevos proyectos
- `IntegrationAgent`: integra herramientas en proyectos nuevos
- `AuditorAgent` ampliado: revisa calidad y coherencia del inventario

## 9. Estado real del proyecto

### Ya implementado y operativo

- pipeline de analisis tecnico del repositorio
- salida estructurada en JSON
- salida legible en Markdown
- soporte para GitHub
- tests de la base funcional

### Ya definido pero no completo

- inventario avanzado de herramientas reutilizables
- clasificacion por capacidades
- recomendacion de herramientas
- integracion automatica en proyectos nuevos
- extraccion semantica con LLM

## 10. Siguientes pasos

Orden recomendado:

1. Mejorar la auditoria del sistema actual
2. Enriquecer el analisis de scripts y dependencias
3. Consolidar el inventario de herramientas reutilizables
4. Implementar clasificacion por capacidades
5. Incorporar seleccion inteligente de archivos y extraccion semantica
6. Activar recomendacion e integracion para proyectos nuevos

## 11. Resumen final

Situacion actual del proyecto:

- ya existe una base funcional y probada
- el sistema ya analiza repositorios reales y genera inventarios
- la arquitectura multiagente esta clara y bien separada
- la parte mas avanzada, orientada a reutilizacion y recomendacion, esta diseñada y parcialmente iniciada, pero aun no terminada

En una frase:

**ya tenemos el motor base funcionando y estamos construyendo la capa inteligente de reutilizacion sobre esa base.**
