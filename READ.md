# Arquitectura Unificada de Subagentes — CI2 Lab

Este documento resume la arquitectura operativa del sistema y queda alineado con la especificacion detallada de `AGENTES_INVENTARIO_CAPACIDADES.md`.

## Objetivo comun

El sistema analiza proyectos locales, detecta herramientas reutilizables, las documenta, las clasifica por capacidades y construye un inventario que despues puede servir para recomendar o integrar herramientas en proyectos nuevos.

Los documentos del repositorio deben leerse asi:

- `AGENTES_INVENTARIO_CAPACIDADES.md` define la especificacion funcional completa.
- `READ.md` define una vista resumida de arquitectura y reparto de responsabilidades.
- `README.md` describe el estado actual de la implementacion.

## Principio de diseno

La arquitectura unificada sigue dos niveles:

1. Un agente principal coordina el flujo de extremo a extremo.
2. Varios agentes especializados ejecutan tareas concretas y devuelven resultados estructurados.

El control de calidad no sustituye a la orquestacion. Por eso:

- `ToolInventoryMainAgent` es el coordinador general.
- `AuditorAgent` es el coordinador de la validacion y el control de calidad.

## Arquitectura general

```text
Usuario
  |
  v
CLI / Entrada del sistema
  |
  v
ToolInventoryMainAgent
  |
  ├── ToolExtractionAgent
  ├── DocumentationAgent
  ├── DependencyAgent
  ├── CapabilityClassifierAgent
  ├── RecommendationAgent
  ├── IntegrationAgent
  └── AuditorAgent
  |
  v
Salidas finales
  |
  ├── inventory/tools/<tool_id>/
  ├── inventory/index/tools_index.json
  ├── inventory/index/capabilities_index.json
  ├── inventory/index/project_tool_map.json
  └── inventory/audit/audit_report.md
```

## Reparto de responsabilidades

### `ToolInventoryMainAgent`

Es el orquestador principal del sistema. Debe:

- recibir proyectos o solicitudes de recomendacion;
- pedir extraccion, documentacion, dependencias y clasificacion;
- generar fichas `tool.yaml` y `README.md`;
- actualizar indices globales;
- solicitar auditoria antes de aceptar resultados;
- pedir confirmacion explicita antes de integrar herramientas en proyectos nuevos.

### `AuditorAgent`

Es el control de calidad del sistema. Debe:

- validar que cada herramienta tenga estructura minima;
- comprobar que capacidades y dependencias tienen evidencia;
- detectar duplicados, mezclas indebidas y datos sensibles;
- emitir advertencias, rechazos o aceptacion con observaciones;
- generar el informe de auditoria.

El auditor supervisa y valida, pero no sustituye al agente principal como coordinador del flujo completo.

## Mapa entre la arquitectura atomica y la actual

| Arquitectura atomica | Arquitectura actual |
|---|---|
| Subagente Scanner | Parte interna de `ToolExtractionAgent` |
| Detector de Lenguajes | Parte de `DependencyAgent` |
| Detector de Dependencias | `DependencyAgent` |
| Detector de Herramientas | `ToolExtractionAgent` |
| Detector de Scripts | `ToolExtractionAgent` y `DependencyAgent` |
| Detector de Documentacion | `DocumentationAgent` |
| Generador de Inventario | `ToolInventoryMainAgent` |
| Generador de Informe | `AuditorAgent` y `ToolInventoryMainAgent` |
| Agente Auditor como coordinador total | `AuditorAgent` como coordinador de validacion |

## Flujo comun del sistema

```text
1. El usuario aporta una carpeta de proyecto o describe un proyecto nuevo.
2. ToolInventoryMainAgent registra la solicitud.
3. ToolExtractionAgent detecta herramientas candidatas.
4. DocumentationAgent extrae documentacion y evidencias.
5. DependencyAgent detecta lenguajes, librerias y requisitos.
6. CapabilityClassifierAgent asigna capacidades con evidencia.
7. ToolInventoryMainAgent genera artefactos de inventario.
8. AuditorAgent valida calidad, coherencia y seguridad.
9. Si hay errores, ToolInventoryMainAgent corrige o marca revision.
10. Si todo es valido, se actualiza el inventario.
11. Si el usuario pide reutilizacion, RecommendationAgent propone herramientas.
12. IntegrationAgent solo integra tras confirmacion explicita.
```

## Reglas comunes

- El sistema trabaja localmente y no depende de APIs externas en la primera fase.
- No se borran archivos originales del proyecto analizado.
- No se inventa informacion sin evidencia trazable.
- El inventario se organiza por capacidades, no solo por repositorios.
- La integracion en proyectos nuevos exige aceptacion explicita del usuario.
- La auditoria es obligatoria antes de aceptar herramientas en el inventario.
