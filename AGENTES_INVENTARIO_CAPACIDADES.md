# Especificación de agentes para Inventario de Capacidades y Herramientas

## 1. Objetivo del sistema

El objetivo es construir un sistema capaz de analizar proyectos de software ya existentes, identificar las herramientas reutilizables que contienen, separarlas en una carpeta común de inventario, documentarlas y permitir que un usuario pueda iniciar un proyecto desde cero recibiendo recomendaciones de herramientas adecuadas.

El sistema debe seguir un enfoque top-down:

1. Primero se define qué es una herramienta válida.
2. Después se define qué información debe tener cada herramienta en el inventario.
3. Después se analiza cada proyecto para encontrar herramientas candidatas.
4. Después se extraen, clasifican y documentan esas herramientas.
5. Finalmente, el agente puede recomendar herramientas existentes para nuevos proyectos.

El sistema debe funcionar inicialmente sin API keys ni acceso a APIs externas. Debe trabajar sobre carpetas locales, repositorios descargados, documentación incluida en el código y archivos accesibles en disco.

---

## 2. Conceptos principales

### 2.1 Proyecto

Un proyecto es una carpeta de trabajo que puede contener una o varias herramientas. Un proyecto puede incluir código, notebooks, documentación, scripts, configuraciones, datos de ejemplo y archivos de ejecución.

Ejemplos:

- Un repositorio de fine-tuning de modelos.
- Un pipeline de análisis de datos.
- Un conjunto de scripts SLURM.
- Una aplicación con backend y frontend.
- Un proyecto de simulación científica.

### 2.2 Herramienta

Una herramienta es una unidad reutilizable de software que permite realizar una tarea concreta.

Una herramienta puede ser:

- Un script ejecutable.
- Una librería interna.
- Un pipeline completo.
- Un notebook parametrizable.
- Un conjunto de scripts relacionados.
- Un módulo de preprocesado.
- Un módulo de entrenamiento.
- Un módulo de inferencia.
- Una utilidad de visualización.
- Una plantilla de proyecto.
- Un script SLURM reutilizable.

No todo archivo de código es una herramienta. Para ser considerada herramienta debe tener al menos una finalidad identificable, entradas o parámetros detectables, y posibilidad razonable de reutilización.

### 2.3 Capacidad

Una capacidad describe lo que una herramienta permite hacer.

Ejemplos:

- Fine-tuning de modelos.
- Inferencia.
- Evaluación de modelos.
- Preprocesado de datos.
- Visualización.
- Simulación HPC.
- Ejecución con SLURM.
- Entrenamiento con GPU.
- Extracción de embeddings.
- Clasificación de imágenes.
- Procesamiento de lenguaje natural.
- Generación de informes.

El inventario final debe estar organizado por capacidades, no solo por repositorios.

---

## 3. Estructura de carpetas objetivo

Codex debe crear o mantener una estructura similar a esta:

```text
repo-root/
├── projects/
│   └── raw/
│       └── <proyecto_original>/
│
├── inventory/
│   ├── tools/
│   │   └── <tool_id>/
│   │       ├── source/
│   │       ├── docs/
│   │       ├── examples/
│   │       ├── tests/
│   │       ├── tool.yaml
│   │       └── README.md
│   │
│   ├── capabilities/
│   │   └── capabilities.yaml
│   │
│   ├── index/
│   │   ├── tools_index.json
│   │   ├── capabilities_index.json
│   │   └── project_tool_map.json
│   │
│   └── audit/
│       ├── audit_report.md
│       ├── audit_findings.json
│       └── unresolved_items.md
│
├── agents/
│   ├── main_agent.md
│   ├── auditor_agent.md
│   ├── documentation_agent.md
│   ├── dependency_agent.md
│   ├── capability_classifier_agent.md
│   ├── extraction_agent.md
│   ├── recommendation_agent.md
│   └── integration_agent.md
│
└── README.md
```

---

## 4. Agentes del sistema

El sistema tendrá un agente principal y varios agentes especializados. El agente principal coordina el flujo. Los agentes especializados no deben tomar decisiones finales sin validación.

---

# 5. Agente principal: `ToolInventoryMainAgent`

## 5.1 Rol

El agente principal es el coordinador del sistema. Su misión es recibir proyectos, analizarlos, separar herramientas, construir el inventario y recomendar herramientas cuando un usuario quiera iniciar un proyecto nuevo.

## 5.2 Responsabilidades

El agente principal debe:

1. Recibir una carpeta de proyecto.
2. Crear un registro del proyecto analizado.
3. Pedir al agente de extracción que detecte herramientas candidatas.
4. Pedir al agente de documentación que extraiga documentación relevante.
5. Pedir al agente de dependencias que detecte lenguajes, librerías y requisitos.
6. Pedir al agente clasificador que asigne capacidades.
7. Crear una carpeta independiente para cada herramienta aceptada.
8. Generar `tool.yaml` y `README.md` para cada herramienta.
9. Actualizar los índices globales.
10. Pedir al agente auditor que revise el resultado.
11. Corregir problemas detectados por el auditor.
12. Recomendar herramientas existentes para proyectos nuevos.
13. Añadir herramientas a un proyecto nuevo solo si el usuario acepta explícitamente.

## 5.3 Entradas

El agente principal puede recibir:

- Ruta local de un proyecto.
- Descripción textual de un proyecto nuevo.
- Solicitud de búsqueda de herramientas.
- Solicitud de recomendación.
- Confirmación del usuario para añadir herramientas.

## 5.4 Salidas

El agente principal debe producir:

- Herramientas separadas en `inventory/tools/`.
- Fichas `tool.yaml`.
- Documentación `README.md` por herramienta.
- Índices globales actualizados.
- Informe de auditoría.
- Recomendaciones de herramientas para nuevos proyectos.

## 5.5 Reglas críticas

El agente principal no debe:

- Inventar información que no esté respaldada por evidencia.
- Borrar archivos originales del proyecto.
- Modificar un proyecto nuevo sin aceptación explícita del usuario.
- Mezclar herramientas distintas en una sola ficha si tienen propósitos claramente diferentes.
- Separar como herramienta código que no sea reutilizable.

---

# 6. Agente extractor: `ToolExtractionAgent`

## 6.1 Rol

Detecta herramientas candidatas dentro de un proyecto.

## 6.2 Qué debe buscar

Debe recorrer el árbol de carpetas y detectar señales como:

```text
README.md
main.py
app.py
train.py
finetune.py
predict.py
inference.py
evaluate.py
preprocess.py
postprocess.py
run.sh
submit.sh
*.sbatch
requirements.txt
pyproject.toml
setup.py
environment.yml
Dockerfile
Makefile
notebooks/*.ipynb
src/
scripts/
docs/
examples/
tests/
```

## 6.3 Criterios para detectar una herramienta

Una carpeta o conjunto de archivos será herramienta candidata si cumple al menos dos de estos criterios:

1. Tiene un punto de entrada ejecutable.
2. Tiene documentación propia.
3. Tiene dependencias identificables.
4. Tiene una tarea funcional clara.
5. Tiene ejemplos de uso.
6. Tiene parámetros configurables.
7. Tiene scripts de ejecución.
8. Puede separarse del resto sin romper todo el proyecto.

## 6.4 Resultado esperado

Debe devolver una lista de herramientas candidatas con:

```yaml
tool_candidate_id: string
name_guess: string
source_paths:
  - string
reason_detected: string
evidence:
  - string
confidence: high | medium | low
requires_review: true | false
```

## 6.5 Casos especiales

Si un proyecto contiene varios módulos relacionados, el agente debe intentar separarlos por función:

- `preprocess` como herramienta de preprocesado.
- `train` como herramienta de entrenamiento.
- `evaluate` como herramienta de evaluación.
- `inference` como herramienta de inferencia.
- `visualization` como herramienta de visualización.

Si no está claro si deben separarse, debe marcar `requires_review: true`.

---

# 7. Agente de documentación: `DocumentationAgent`

## 7.1 Rol

Extrae y resume la documentación existente de cada herramienta candidata.

## 7.2 Fuentes de documentación

Debe leer:

- README.
- Archivos Markdown.
- Docstrings.
- Comentarios relevantes.
- Celdas Markdown de notebooks.
- Argumentos de CLI.
- Mensajes de ayuda tipo `argparse`.
- Ejemplos en scripts.
- Carpetas `docs/` y `examples/`.

## 7.3 Qué debe extraer

Debe intentar extraer:

```yaml
purpose: string
inputs:
  - string
outputs:
  - string
usage_examples:
  - string
configuration:
  - string
limitations:
  - string
assumptions:
  - string
documentation_sources:
  - file: string
    evidence: string
```

## 7.4 Regla de evidencia

Toda afirmación importante debe poder asociarse a un archivo fuente. Si no hay evidencia suficiente, debe marcarse como inferencia con confianza media o baja.

---

# 8. Agente de dependencias: `DependencyAgent`

## 8.1 Rol

Detecta lenguajes, frameworks, librerías, dependencias de sistema y requisitos de ejecución.

## 8.2 Fuentes

Debe analizar:

- `requirements.txt`
- `pyproject.toml`
- `setup.py`
- `environment.yml`
- `package.json`
- `Cargo.toml`
- `go.mod`
- `pom.xml`
- `build.gradle`
- `Dockerfile`
- imports de Python
- includes de C/C++
- scripts Bash
- directivas SLURM

## 8.3 Salida esperada

```yaml
languages:
  - Python
  - Bash
frameworks:
  - PyTorch
  - Transformers
dependencies:
  python:
    - torch
    - transformers
  system:
    - cuda
    - gcc
execution_requirements:
  cpu: true
  gpu: true
  slurm: false
  docker: false
  conda: true
confidence: high | medium | low
```

## 8.4 Reglas

Si se detecta `torch.cuda`, `cuda`, `nvidia-smi` o `--gres=gpu`, marcar `gpu: true`.

Si se detecta `#SBATCH`, `sbatch`, `srun`, `squeue`, marcar `slurm: true`.

Si se detecta `environment.yml`, marcar `conda: true`.

Si se detecta `Dockerfile`, marcar `docker: true`.

---

# 9. Agente clasificador de capacidades: `CapabilityClassifierAgent`

## 9.1 Rol

Clasifica cada herramienta según una taxonomía de capacidades.

## 9.2 Taxonomía inicial

La taxonomía inicial debe estar en:

```text
inventory/capabilities/capabilities.yaml
```

Debe incluir al menos estas familias:

```yaml
ai_ml:
  - fine_tuning
  - training
  - inference
  - evaluation
  - embeddings
  - rag
  - computer_vision
  - nlp
  - time_series
  - model_serving

data:
  - data_ingestion
  - preprocessing
  - cleaning
  - transformation
  - visualization
  - reporting

hpc:
  - slurm_execution
  - mpi
  - openmp
  - cuda
  - distributed_training
  - batch_processing

software:
  - api_backend
  - frontend
  - cli_tool
  - automation
  - testing
  - packaging

scientific:
  - simulation
  - optimization
  - numerical_methods
  - signal_processing
  - image_analysis
```

## 9.3 Reglas de clasificación

Debe asignar capacidades usando evidencias. Ejemplos:

| Evidencia | Capacidad |
|---|---|
| `finetune.py`, `LoRA`, `PEFT` | `fine_tuning` |
| `train.py`, `fit`, `epochs` | `training` |
| `predict.py`, `inference.py` | `inference` |
| `evaluate.py`, `metrics` | `evaluation` |
| `faiss`, `chromadb`, `retriever` | `rag` |
| `opencv`, `torchvision`, `yolo` | `computer_vision` |
| `transformers`, `tokenizer`, `bert`, `llama` | `nlp` |
| `#SBATCH`, `sbatch`, `srun` | `slurm_execution` |
| `mpi4py`, `mpirun`, `mpiexec` | `mpi` |
| `openmp`, `omp_get_thread_num` | `openmp` |
| `cuda`, `torch.cuda`, `cupy` | `cuda` |
| `FastAPI`, `Flask`, `Django` | `api_backend` |
| `React`, `Next.js`, `Vue` | `frontend` |

## 9.4 Salida esperada

```yaml
capabilities:
  - id: fine_tuning
    confidence: high
    evidence:
      - file: train.py
        reason: contains PEFT/LoRA training loop
  - id: slurm_execution
    confidence: medium
    evidence:
      - file: submit.sh
        reason: contains sbatch command
```

---

# 10. Agente integrador: `IntegrationAgent`

## 10.1 Rol

Añade herramientas existentes a un proyecto nuevo cuando el usuario lo acepta.

## 10.2 Flujo obligatorio

1. Recibir descripción del proyecto nuevo.
2. Pedir al agente recomendador herramientas candidatas.
3. Mostrar recomendación al usuario.
4. Esperar aceptación explícita.
5. Solo después copiar o referenciar herramientas en el proyecto.
6. Generar instrucciones de uso.
7. Registrar qué herramientas se añadieron.

## 10.3 Reglas críticas

El agente integrador no debe modificar un proyecto sin confirmación explícita.

Confirmaciones válidas:

```text
sí, añádelas
acepto
puedes añadirlas
integra esas herramientas
```

Confirmaciones no válidas:

```text
vale
ok
me gusta
interesante
```

En caso de duda, debe pedir confirmación.

## 10.4 Formas de integración

El agente puede integrar de tres maneras:

### Copia directa

Copia la herramienta a:

```text
<new_project>/tools/<tool_id>/
```

### Referencia ligera

Crea un archivo:

```text
<new_project>/tools_manifest.yaml
```

con referencias al inventario.

### Plantilla

Copia solo archivos mínimos de arranque:

```text
<new_project>/starter_templates/<tool_id>/
```

## 10.5 Salida esperada

Debe generar:

```yaml
integrated_tools:
  - tool_id: string
    integration_mode: copy | reference | template
    destination: string
    added_files:
      - string
    usage_notes: string
```

---

# 11. Agente recomendador: `RecommendationAgent`

## 11.1 Rol

Sugiere herramientas correctas cuando un usuario quiere hacer un proyecto desde cero.

## 11.2 Entrada

Ejemplo de entrada:

```text
Quiero hacer un proyecto de fine-tuning de un LLM con datos propios y ejecutarlo en GPU.
```

## 11.3 Proceso

El agente debe:

1. Extraer intención del usuario.
2. Detectar capacidades necesarias.
3. Buscar herramientas del inventario que cubran esas capacidades.
4. Ordenarlas por compatibilidad.
5. Explicar por qué recomienda cada herramienta.
6. Señalar huecos si no existe una herramienta adecuada.

## 11.4 Salida esperada

```yaml
project_goal: string
required_capabilities:
  - fine_tuning
  - nlp
  - cuda
recommended_tools:
  - tool_id: llm_finetune_pipeline
    reason: Covers fine_tuning, nlp and cuda
    confidence: high
    integration_options:
      - copy
      - template
missing_capabilities:
  - dataset_validation
questions_for_user:
  - What model family will be used?
```

## 11.5 Respuesta al usuario

Debe ser clara:

```text
Para este proyecto recomiendo estas herramientas:

1. llm_finetune_pipeline
   Motivo: permite fine-tuning con Transformers y GPU.

2. slurm_gpu_template
   Motivo: permite lanzar el entrenamiento en clúster con GPU.

Falta una herramienta específica de validación de dataset.

¿Quieres que añada estas herramientas al proyecto?
```

---

# 12. Agente auditor: `AuditorAgent`

## 12.1 Rol

Comprueba que todo esté bien hecho antes de aceptar una herramienta en el inventario.

El auditor debe actuar como control de calidad. No crea herramientas nuevas. No recomienda herramientas. Solo valida, detecta errores y exige correcciones.

## 12.2 Qué debe auditar

Debe revisar:

1. Que cada herramienta tenga carpeta propia.
2. Que cada herramienta tenga `tool.yaml`.
3. Que cada herramienta tenga `README.md`.
4. Que las capacidades asignadas tengan evidencia.
5. Que las dependencias estén justificadas.
6. Que no haya herramientas duplicadas.
7. Que no se hayan mezclado herramientas distintas.
8. Que no se haya inventado información.
9. Que el estado de confianza sea coherente.
10. Que los índices globales estén actualizados.
11. Que las rutas existan.
12. Que no se hayan copiado datos sensibles innecesarios.

## 12.3 Checklist de auditoría

Para cada herramienta:

```yaml
tool_id: string
checks:
  has_tool_yaml: pass | fail
  has_readme: pass | fail
  has_source_folder: pass | fail
  has_name: pass | fail
  has_description: pass | fail
  has_capabilities: pass | fail
  capabilities_have_evidence: pass | fail
  dependencies_have_evidence: pass | fail
  usage_documented: pass | warning | fail
  confidence_is_reasonable: pass | warning | fail
  no_duplicate_detected: pass | warning | fail
  no_sensitive_data: pass | warning | fail
status: accepted | accepted_with_warnings | rejected
required_fixes:
  - string
```

## 12.4 Criterios de rechazo

El auditor debe rechazar una herramienta si:

- No tiene finalidad clara.
- No tiene evidencia suficiente.
- No tiene `tool.yaml`.
- No tiene descripción.
- Sus capacidades son inventadas.
- La carpeta contiene datos privados o innecesarios.
- Se mezclan varias herramientas sin separación.

## 12.5 Informe de auditoría

Debe generar:

```text
inventory/audit/audit_report.md
```

con:

```markdown
# Informe de auditoría

## Resumen

- Herramientas analizadas:
- Aceptadas:
- Aceptadas con avisos:
- Rechazadas:

## Problemas detectados

## Correcciones necesarias

## Recomendaciones
```

---

# 13. Formato obligatorio de `tool.yaml`

Cada herramienta debe tener un archivo:

```text
inventory/tools/<tool_id>/tool.yaml
```

Formato mínimo:

```yaml
tool_id: string
name: string
short_description: string
long_description: string
source_project: string
source_paths:
  - string
category: string
capabilities:
  - id: string
    confidence: high | medium | low
    evidence:
      - file: string
        reason: string
languages:
  - string
dependencies:
  python:
    - string
  system:
    - string
execution:
  local: true | false
  gpu: true | false
  slurm: true | false
  docker: true | false
  conda: true | false
inputs:
  - string
outputs:
  - string
usage_examples:
  - string
documentation:
  sources:
    - string
  quality: high | medium | low
status: active | experimental | incomplete | deprecated
confidence: high | medium | low
created_at: string
updated_at: string
review:
  audited: true | false
  audit_status: accepted | accepted_with_warnings | rejected | pending
  auditor_notes: string
```

---

# 14. Formato obligatorio de `README.md` por herramienta

Cada herramienta debe tener:

```text
inventory/tools/<tool_id>/README.md
```

Estructura:

```markdown
# <Nombre de la herramienta>

## Descripción

## Capacidades

## Entradas

## Salidas

## Dependencias

## Modo de ejecución

## Ejemplo de uso

## Evidencias utilizadas

## Estado de documentación

## Limitaciones conocidas
```

---

# 15. Índices globales

## 15.1 `tools_index.json`

Debe listar todas las herramientas:

```json
[
  {
    "tool_id": "string",
    "name": "string",
    "capabilities": ["fine_tuning", "cuda"],
    "status": "active",
    "confidence": "high",
    "path": "inventory/tools/<tool_id>"
  }
]
```

## 15.2 `capabilities_index.json`

Debe organizar herramientas por capacidades:

```json
{
  "fine_tuning": ["llm_finetune_pipeline"],
  "cuda": ["llm_finetune_pipeline", "gpu_slurm_template"]
}
```

## 15.3 `project_tool_map.json`

Debe mapear proyectos originales a herramientas detectadas:

```json
{
  "project_alpha": [
    "preprocessing_pipeline",
    "training_pipeline",
    "evaluation_tool"
  ]
}
```

---

# 16. Flujo completo de análisis de un proyecto

```text
1. Usuario aporta carpeta de proyecto.
2. ToolInventoryMainAgent registra el proyecto.
3. ToolExtractionAgent detecta herramientas candidatas.
4. DocumentationAgent extrae documentación.
5. DependencyAgent extrae dependencias y requisitos.
6. CapabilityClassifierAgent asigna capacidades.
7. ToolInventoryMainAgent crea carpetas de herramientas.
8. ToolInventoryMainAgent genera tool.yaml y README.md.
9. ToolInventoryMainAgent actualiza índices.
10. AuditorAgent revisa resultados.
11. Si hay errores, ToolInventoryMainAgent corrige.
12. Si pasa auditoría, la herramienta queda aceptada.
```

---

# 17. Flujo completo de recomendación para proyecto nuevo

```text
1. Usuario describe el proyecto que quiere crear.
2. RecommendationAgent extrae capacidades necesarias.
3. RecommendationAgent busca herramientas compatibles en el inventario.
4. RecommendationAgent devuelve una propuesta razonada.
5. Usuario acepta o rechaza.
6. Si acepta, IntegrationAgent añade las herramientas.
7. IntegrationAgent genera instrucciones de uso.
8. AuditorAgent revisa que la integración no haya roto nada.
```

---

# 18. Ejemplo práctico

## Entrada del usuario

```text
Quiero crear un proyecto para hacer fine-tuning de un modelo LLM con datos propios y ejecutarlo en GPU.
```

## Capacidades detectadas

```yaml
required_capabilities:
  - fine_tuning
  - nlp
  - cuda
  - dataset_preprocessing
  - evaluation
```

## Recomendación esperada

```text
Herramientas recomendadas:

1. llm_finetune_pipeline
   Cubre: fine_tuning, nlp, cuda.
   Confianza: alta.

2. dataset_preprocessing_tool
   Cubre: dataset_preprocessing.
   Confianza: media.

3. model_evaluation_tool
   Cubre: evaluation.
   Confianza: alta.

No se ha encontrado una herramienta específica para validación automática de datasets.
```

## Acción permitida solo con aceptación

```text
¿Quieres que añada estas herramientas al proyecto?
```

Si el usuario responde afirmativamente de forma clara, se integran.

---

# 19. Reglas de seguridad y conservación

El sistema debe:

- No borrar archivos originales.
- No modificar proyectos sin confirmación.
- No copiar datasets grandes al inventario salvo que sean ejemplos mínimos.
- No copiar credenciales.
- No copiar `.env` con secretos.
- No copiar claves SSH.
- No copiar tokens.
- No subir nada a servicios externos.
- Trabajar localmente.

El auditor debe revisar especialmente:

```text
.env
*.pem
*.key
id_rsa
credentials.json
secrets.yaml
tokens.txt
```

---

# 20. Criterios de calidad

Una herramienta está bien inventariada si:

1. Tiene finalidad clara.
2. Tiene capacidades asignadas.
3. Tiene evidencias.
4. Tiene dependencias identificadas.
5. Tiene instrucciones básicas de uso.
6. Tiene nivel de confianza.
7. Ha pasado auditoría.
8. Está indexada por capacidad.

---

# 21. Prioridad de implementación para Codex

Codex debe implementar en este orden:

## Fase 1

1. Crear estructura de carpetas.
2. Definir `capabilities.yaml`.
3. Implementar detección básica de herramientas candidatas.
4. Generar `tool.yaml` mínimo.
5. Generar `README.md` mínimo.
6. Crear `tools_index.json`.

## Fase 2

1. Añadir extracción de dependencias.
2. Añadir clasificación de capacidades.
3. Añadir `capabilities_index.json`.
4. Añadir auditoría básica.

## Fase 3

1. Añadir recomendador de herramientas.
2. Añadir integración en proyecto nuevo.
3. Añadir auditoría de integración.
4. Mejorar documentación generada.

---

# 22. Comportamiento esperado del sistema

El sistema debe ser incremental.

Si falta información, no debe fallar. Debe marcar campos como incompletos:

```yaml
status: incomplete
confidence: low
```

Si encuentra documentación clara, debe aumentar confianza.

Si encuentra contradicciones, debe marcar revisión manual.

Si no puede clasificar una herramienta, debe usar:

```yaml
capabilities:
  - id: unknown
    confidence: low
```

---

# 23. Resultado final esperado

Al finalizar el análisis de varios proyectos, el repositorio debe permitir responder preguntas como:

- ¿Qué herramientas existen?
- ¿Qué capacidades tiene el laboratorio?
- ¿Qué herramientas sirven para fine-tuning?
- ¿Qué herramientas requieren GPU?
- ¿Qué herramientas se ejecutan con SLURM?
- ¿Qué herramientas tienen documentación incompleta?
- ¿Qué herramientas puedo reutilizar para un proyecto nuevo?
- ¿Qué herramientas debería añadir a mi proyecto si quiero hacer una tarea concreta?

---

# 24. Principio final

El sistema no debe limitarse a listar archivos o repositorios.

Debe construir un inventario de capacidades reutilizables.

El agente principal construye y recomienda.

Los agentes especializados extraen, clasifican, documentan e integran.

El agente auditor garantiza calidad, coherencia y seguridad.
