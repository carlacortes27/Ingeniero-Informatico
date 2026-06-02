# Inventario de Capacidades y Herramientas

Este repositorio combina dos piezas:

- una base de arquitectura modular para analizar repositorios locales;
- una implementacion inicial de inventario de herramientas orientado a capacidades.

## Documentacion del repo

- `AGENTES_INVENTARIO_CAPACIDADES.md`: especificacion funcional detallada y documento canonico.
- `READ.md`: arquitectura unificada y reparto de responsabilidades entre agentes.
- `README.md`: vision general del repositorio, estado actual y forma de uso.

## Estado actual

La implementacion disponible cubre una base de Fase 1:

- crea la estructura base de inventario y agentes;
- define una taxonomia inicial de capacidades en `inventory/capabilities/capabilities.yaml`;
- analiza proyectos locales dentro de `projects/raw/`;
- detecta herramientas candidatas usando heuristicas de archivos comunes;
- genera una carpeta por herramienta en `inventory/tools/`;
- genera `tool.yaml`, `README.md` por herramienta y `tools_index.json`.

Ademas, el repositorio conserva la estructura Python inicial en `src/ci2_lab/` para evolucionar hacia una CLI y agentes reales.

## Uso de la fase actual

1. Coloca uno o mas proyectos en `projects/raw/`.
2. Ejecuta:

```bash
python3 scripts/inventory_phase1.py
```

Opcionalmente puedes analizar una ruta concreta:

```bash
python3 scripts/inventory_phase1.py --project projects/raw/mi_proyecto
```

## Estructura relevante

```text
projects/raw/                  proyectos de entrada
inventory/tools/               herramientas inventariadas
inventory/capabilities/        taxonomia de capacidades
inventory/index/               indices globales
inventory/audit/               salidas de auditoria
agents/                        descripciones funcionales de agentes
src/ci2_lab/                   base Python del sistema
scripts/inventory_phase1.py    generador inicial del inventario
```

## Limitaciones actuales

- La clasificacion avanzada de capacidades aun no esta implementada.
- La extraccion de dependencias es minima.
- La auditoria y las recomendaciones quedan para fases posteriores.
- La estructura Python en `src/ci2_lab/` sigue siendo un esqueleto inicial.
