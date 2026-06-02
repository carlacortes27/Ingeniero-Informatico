# Inventario de Capacidades y Herramientas

Implementacion inicial de la Fase 1 descrita en `AGENTES_INVENTARIO_CAPACIDADES.md`.

## Que hace ahora

- Crea la estructura base de inventario y agentes.
- Define una taxonomia inicial de capacidades en `inventory/capabilities/capabilities.yaml`.
- Analiza proyectos locales dentro de `projects/raw/`.
- Detecta herramientas candidatas usando heuristicas de archivos comunes.
- Genera una carpeta por herramienta en `inventory/tools/`.
- Genera `tool.yaml`, `README.md` y `tools_index.json`.

## Uso

1. Coloca uno o mas proyectos en `projects/raw/`.
2. Ejecuta:

```bash
python3 scripts/inventory_phase1.py
```

Opcionalmente puedes analizar una ruta concreta:

```bash
python3 scripts/inventory_phase1.py --project projects/raw/mi_proyecto
```

## Limitaciones actuales

- La clasificacion avanzada de capacidades aun no esta implementada.
- La extraccion de dependencias es minima.
- La auditoria y las recomendaciones quedan para fases posteriores.
