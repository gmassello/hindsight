# Plan de ejecución — Track "Agents That Do Real Work"

## Hindsight · Build with DataHub: The Agent Hackathon

> Documento técnico de ejecución · German Massello · 2 de agosto de 2026
> **Cierre: lunes 10 de agosto, 18:00 ART** (5:00pm EDT) · 8 días

---

## 1. Qué premia exactamente este track

La definición oficial del track, palabra por palabra:

> Agentes autónomos que **leen DataHub para entender qué está conectado con qué, toman acción, y escriben los resultados de vuelta**.

Son tres verbos y hay que cumplir los tres. La mayoría de los participantes va a cumplir el primero (leer) y quizás el segundo (razonar), pero **muy pocos van a escribir de vuelta**, porque requiere habilitar las mutation tools y diseñar una capa de seguridad. Ahí está tu ventaja competitiva.

Traducido a decisiones de diseño:

| Verbo | Qué tiene que verse en el demo | Tools |
|---|---|---|
| **Leer** | Recorrido de linaje multi-hop, no una búsqueda plana | `search`, `get_entities`, `get_lineage`, `get_lineage_paths_between`, `list_schema_fields`, `get_dataset_queries` |
| **Actuar** | Una decisión con consecuencias, no un resumen bonito | Scoring de impacto, hipótesis de causa raíz ranqueadas, plan de acción |
| **Escribir de vuelta** | El estado de DataHub cambia y se ve en su UI | `add_tags`, `update_description`, `add_owners`, `set_domains`, `save_document` |

**Regla de oro para el video**: si al final del demo no se ve la UI de DataHub con algo que el agente escribió, no cumpliste el track.

---

## 2. La tesis

> **Hindsight es el on-call de tu plataforma de datos. Cuando algo se rompe, recorre el linaje de DataHub para calcular quién se ve afectado, propone la causa raíz apoyándose en incidentes que ya resolviste antes, y escribe el postmortem de vuelta en DataHub — de modo que el próximo diagnóstico arranque desde donde terminó este.**

El loop cerrado es el argumento. No es un chatbot sobre metadata: es un sistema que se vuelve más inteligente con cada uso, y esa mejora vive **dentro de DataHub**, no en una base de datos paralela tuya. Ese detalle es lo que convierte la integración de "profunda" en "inevitable".

### Por qué este ángulo gana

Con ~764 inscriptos, la distribución esperada de proyectos es previsible: mucho text-to-SQL (el Analytics Agent ya existe y es open source, así que es el camino obvio), varios chat-with-your-catalog, algunos generadores de documentación. Casi todos van a ser **read-only**.

Tu proyecto se diferencia en tres ejes simultáneos:

1. **Escribe de vuelta** — el track lo pide explícitamente y pocos lo harán
2. **Usa el grafo como grafo** — recorrido multi-hop con scoring, no un `search` y listo
3. **Tiene memoria** — el sistema acumula conocimiento, y ese conocimiento queda en DataHub

---

## 3. Alcance: qué entra y qué no

Con 8 días de tardes, el mayor riesgo no es técnico, es de alcance. Esto es lo que **no** vas a construir:

| Fuera de alcance | Por qué |
|---|---|
| Ejecución de SQL contra un warehouse real | No lo necesitás y agrega superficie de fallo enorme |
| Integración con PagerDuty / Slack / Jira | Suena bien en el pitch, no suma en la rúbrica |
| Autenticación multi-usuario | Es un demo, no un SaaS |
| Detección automática de incidentes (monitoreo) | El agente recibe la alerta, no la genera |
| Fine-tuning o embeddings propios | `search_documents` de DataHub ya te da recuperación semántica |
| Soporte multi-warehouse | Un solo entorno, `showcase-ecommerce` |

Lo que **sí** entra, en orden de prioridad no negociable:

1. Agente que diagnostica end-to-end sobre el linaje real
2. Write-back a DataHub con aprobación humana
3. Memoria de postmortems que alimenta el diagnóstico siguiente
4. UI con timeline de evidencia en streaming
5. Tres escenarios reproducibles + carpeta `examples/`

Si el día 7 vas retrasado, se cae el punto 4 antes que cualquier otro. Un CLI con salida bien formateada califica igual.

---

## 4. Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND  React + Vite + TS          [reciclado de Recall]      │
│  ┌────────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ Timeline de    │ │ Grafo de     │ │ Panel "ya vimos esto"  │  │
│  │ evidencia (SSE)│ │ blast radius │ │ (incidentes similares) │  │
│  └────────────────┘ └──────────────┘ └────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Plan de acción propuesto  →  [ Aprobar ] [ Rechazar ]     │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ SSE
┌─────────────────────────────▼────────────────────────────────────┐
│  BACKEND  FastAPI                      [reciclado de Recall]     │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │  ORQUESTADOR DE FASES  (máquina de estados determinista) │    │
│   │  intake → resolve → recall → impact → root_cause →       │    │
│   │           → propose → [ human gate ] → commit → learn    │    │
│   └───────────────────────┬─────────────────────────────────┘    │
│                           │                                       │
│   ┌───────────────────────▼──────────┐  ┌──────────────────────┐ │
│   │  CAPA LLM proveedor-agnóstica    │  │  CAPA DE ESCRITURA   │ │
│   │  Anthropic / Gemini / Bedrock    │  │  dry-run + auditoría │ │
│   │        [reciclado de Recall]     │  │        [nuevo]       │ │
│   └───────────────────────┬──────────┘  └──────────┬───────────┘ │
└───────────────────────────┼────────────────────────┼─────────────┘
                            │                        │
                  ┌─────────▼────────────────────────▼──────────┐
                  │      CLIENTE MCP DE DATAHUB      [nuevo]     │
                  │      + fallback por SDK de Python            │
                  └─────────────────────┬───────────────────────┘
                                        │
                  ┌─────────────────────▼───────────────────────┐
                  │  DataHub (self-hosted, quickstart)          │
                  │  MCP en http://<gms-host>:8080/mcp          │
                  │  Datapack: showcase-ecommerce (1.049 ent.)  │
                  └─────────────────────────────────────────────┘
```

### Decisión de diseño clave: pipeline de fases, no ReAct suelto

Un loop ReAct libre es más "impresionante" en el papel pero es una lotería en un demo grabado: a veces el modelo no llama la tool correcta, a veces se va por las ramas, a veces tarda 90 segundos. **Vas a grabar un video de 3 minutos.** Necesitás determinismo.

La arquitectura correcta es una **máquina de estados determinista con un LLM adentro de cada fase**. El orquestador decide *qué* fase corre y *qué* tools están disponibles en esa fase; el LLM decide *cómo* interpretar los resultados. Ganás:

- Cada fase emite un evento al timeline → el streaming se ve espectacular y es predecible
- Podés testear cada fase por separado
- Si una fase falla, degradás con elegancia en vez de romper todo
- El jurado ve una arquitectura pensada, no un `while True` con tools

Documentá esta decisión en el README. El criterio "calidad técnica" se gana con decisiones justificadas, no con líneas de código.

---

## 5. El agente, fase por fase

### Fase 0 — `intake`

Entrada: texto libre. *"fct_orders viene con nulls en customer_id desde las 03:00 UTC"*, o un JSON de alerta de dbt/Monte Carlo/Airflow.

Salida: un `Incident` estructurado (Pydantic) con `raw_text`, `mentioned_assets[]`, `symptom_type` (nulls / freshness / schema / volume / failure), `detected_at`.

Sin tools. Solo un LLM con salida estructurada. Barato y rápido.

### Fase 1 — `resolve`

Tools: `search` → `get_entities`

Resolver los nombres mencionados en lenguaje natural a **URNs concretas de DataHub**. Si hay ambigüedad (dos tablas se llaman parecido), el agente elige la de mayor señal —más consumidores downstream, tiene owner, tiene domain— y **deja registrada la ambigüedad en el timeline**. Ese detalle de honestidad epistémica impresiona a los jueces.

Salida: `resolved_asset: EntityRef` + `alternatives[]`.

### Fase 2 — `recall` ★ (el diferenciador)

Tools: `search_documents`, `grep_documents`

**Esta fase va acá y no al final, y esa es la decisión de producto más importante del proyecto.**

La forma obvia sería investigar primero y mostrar "incidentes similares" como un adorno al costado. La forma correcta es **buscar en la memoria antes de investigar, y dejar que lo recuperado dirija la investigación**. Si hace tres meses este mismo dataset se rompió por un cambio de esquema aguas arriba en `raw_customers`, el agente debería ir a mirar `raw_customers` *primero*.

Salida: `prior_incidents[]` con similitud, resolución previa, y **`investigation_hints[]`** — las URNs y los tipos de causa que la memoria sugiere revisar con prioridad.

En el timeline esto se ve como: *"Encontré 2 incidentes similares. Voy a revisar `raw_customers` primero porque en marzo fue el origen."* Ese es el momento del video.

### Fase 3 — `impact`

Tools: `get_lineage` (dirección DOWNSTREAM, 3+ hops)

Recorrer el grafo aguas abajo y calcular el radio de impacto. Fórmula sugerida, defendible y simple:

```
impacto(consumidor) = peso_tipo × decaimiento_hops × multiplicador_criticidad

  peso_tipo:            Dashboard = 3 · MLModel/MLFeature = 3
                        dbt model = 2 · Dataset = 1
  decaimiento_hops:     1 / (1 + hops)
  multiplicador:        ×1.5 si tiene owner asignado
                        ×2.0 si tiene glossary term de Tier1 / PII
                        ×1.3 si pertenece a un domain

impacto_total = Σ impacto(consumidor)
```

Salida: `blast_radius` con lista ordenada de consumidores afectados, el total, y **los owners a notificar** (agrupados, deduplicados). "A quién hay que avisar" es una respuesta accionable; "qué se rompió" es solo información.

### Fase 4 — `root_cause`

Tools: `get_lineage` (UPSTREAM), `get_lineage_paths_between`, `list_schema_fields`, `get_dataset_queries`, `get_entities`

Guiada por los `investigation_hints` de la fase 2. Genera hipótesis ranqueadas, cada una con evidencia explícita:

| Hipótesis | Cómo se detecta |
|---|---|
| **Schema drift upstream** | `list_schema_fields` sobre los ancestros: columna que desapareció, cambió de tipo, o se volvió nullable |
| **Cambio en la query de transformación** | `get_dataset_queries` sobre el asset y sus padres directos |
| **Incidente upstream activo** | Un ancestro ya tiene el tag `hindsight:degraded` (escrito por una corrida anterior — el sistema se lee a sí mismo) |
| **Ruta de propagación** | `get_lineage_paths_between` entre el asset roto y el ancestro sospechoso: muestra el camino exacto |
| **Precedente histórico** | La memoria de la fase 2 ya vio este patrón |

Salida: `hypotheses[]` ordenadas por confianza, cada una con `evidence[]` citando URNs concretas. **Nunca una sola respuesta con tono de certeza** — un on-call honesto da hipótesis ranqueadas, y eso es exactamente lo que un ingeniero senior valora.

### Fase 5 — `propose`

Sin tools de DataHub. El LLM arma un **plan de acción** en modo dry-run:

```json
{
  "mutations": [
    { "tool": "add_tags", "urn": "urn:li:dataset:(...,fct_orders,PROD)",
      "args": { "tags": ["hindsight:degraded"] },
      "rationale": "Asset con incidente activo confirmado" },
    { "tool": "add_tags", "urn": "urn:li:dashboard:(...,exec_revenue)",
      "args": { "tags": ["hindsight:impacted"] },
      "rationale": "Consumidor a 2 hops, score de impacto 4.5" },
    { "tool": "update_description", "urn": "...",
      "args": { "description": "⚠️ Incidente activo desde 2026-08-08 03:00 UTC..." },
      "rationale": "Avisar a quien abra el asset en la UI" },
    { "tool": "add_owners", "urn": "...",
      "args": { "owners": ["urn:li:corpuser:data-platform"] },
      "rationale": "Asset crítico sin owner — gap de governance detectado" }
  ],
  "document": { "tool": "save_document", "title": "Incident 2026-08-08: nulls en fct_orders.customer_id" }
}
```

Se renderiza como un diff legible. **Nada se ejecuta todavía.**

### Fase 6 — `commit` (detrás del human gate)

Tools: `add_tags`, `update_description`, `add_owners`, `set_domains`

Se ejecuta **solo tras aprobación explícita**. Cada mutación se registra en un log de auditoría con timestamp, tool, URN, argumentos y el motivo. El log se expone en la UI y se guarda en `examples/`.

> **Modo `--auto-approve`**: implementalo pero dejalo apagado por defecto y documentá por qué. "El agente puede correr autónomo, pero el default es pedir permiso" es una postura de diseño madura que los jueces de una empresa de governance van a valorar. Es exactamente su discurso.

### Fase 7 — `learn` ★ (cierra el loop)

Tool: `save_document`

Guarda el postmortem estructurado como documento en DataHub. Ese documento es lo que la fase 2 de la **próxima** corrida va a recuperar.

Esquema del postmortem:

```markdown
# Incidente {id} — {título}

**Asset**: {urn}
**Detectado**: {timestamp}
**Síntoma**: {tipo} — {descripción}
**Estado**: {activo | resuelto}

## Radio de impacto
{N} consumidores afectados en {M} hops. Score: {score}
Owners notificados: {lista}
| Asset | Tipo | Hops | Score |
|---|---|---|---|

## Hipótesis de causa raíz
1. {hipótesis} — confianza {X}%
   Evidencia: {urns citadas}

## Resolución
{completado por el humano, o inferido}

## Señales de detección
{qué mirar para detectarlo antes la próxima vez}

## Tags
{síntoma}, {plataforma}, {tipo de causa}
```

**El momento de cierre del video**: correr el mismo escenario dos veces. La primera vez el agente investiga desde cero y tarda. La segunda vez, la fase 2 recupera el postmortem que él mismo escribió y va directo al grano. *Eso* es "agents that do real work".

---

## 6. Setup técnico

### DataHub local

```bash
# Prerrequisitos: Docker + Docker Compose v2 + Python 3.10+
# Docker necesita: 2 CPUs, 8GB RAM, 2GB swap, 13GB disco

pip install acryl-datahub          # versión actual: 1.6.0.x
datahub docker quickstart          # UI en http://localhost:9002 (datahub/datahub)

datahub init --username datahub --password datahub
datahub datapack load showcase-ecommerce
```

Comandos de rescate: `datahub docker quickstart --stop` · `datahub docker nuke` (reset total) · `datahub docker quickstart --backup`

### MCP server con mutaciones habilitadas

El endpoint self-hosted es `http://<gms-host>:8080/mcp`. **Las mutation tools están apagadas por defecto** y sin ellas no cumplís el track:

```bash
TOOLS_IS_MUTATION_ENABLED=true      # ← IMPRESCINDIBLE, default false
TOOLS_IS_USER_ENABLED=true          # para add_owners
SEMANTIC_SEARCH_ENABLED=true        # ← mejora mucho la fase de memoria
TOOL_RESPONSE_TOKEN_LIMIT=80000     # subilo si el linaje viene truncado
```

Verificá esto el **día 0**. Si las mutaciones no arrancan en tu versión, el plan B es escribir vía el SDK de Python directamente (`acryl-datahub`), lo cual sigue calificando aunque es menos elegante.

### Agent Context Kit

```bash
pip install datahub-agent-context   # requiere Python 3.10+ y un PAT
```

Expone builders de tools para LangChain y Google ADK. El flag `include_mutations` controla si las tools de escritura entran al toolset — asegurate de pasarlo en `True` para las fases 6 y 7, y en `False` para las fases 1 a 4. **Separar el toolset por fase evita que el modelo escriba cuando debería estar leyendo**, y es un detalle de ingeniería que vale la pena mencionar en el README.

### Variables de entorno del proyecto

Seguí la convención del Analytics Agent oficial, así el jurado reconoce el patrón:

```bash
DATAHUB_GMS_URL=http://localhost:8080
DATAHUB_GMS_TOKEN=<personal access token>
LLM_PROVIDER=anthropic              # anthropic | openai | google | bedrock
LLM_MODEL=<modelo principal>
HINDSIGHT_AUTO_APPROVE=false        # human gate activado por defecto
HINDSIGHT_MAX_HOPS=3
```

---

## 7. Estructura del repo

```
hindsight/
├── LICENSE                      # Apache 2.0 — desde el primer commit
├── README.md                    # arquitectura, quickstart, decisiones de diseño
├── docker-compose.yml           # levanta todo con un comando (plan B del deploy)
├── .env.example
│
├── backend/
│   ├── src/hindsight/
│   │   ├── agent/
│   │   │   ├── orchestrator.py      # la máquina de estados
│   │   │   └── phases/
│   │   │       ├── intake.py
│   │   │       ├── resolve.py
│   │   │       ├── recall.py        # ★
│   │   │       ├── impact.py
│   │   │       ├── root_cause.py
│   │   │       ├── propose.py
│   │   │       ├── commit.py
│   │   │       └── learn.py         # ★
│   │   ├── datahub/
│   │   │   ├── mcp_client.py        # cliente MCP
│   │   │   ├── sdk_fallback.py      # plan B si el MCP falla
│   │   │   └── lineage.py           # recorrido + scoring
│   │   ├── llm/                     # capa proveedor-agnóstica [de Recall]
│   │   ├── memory/
│   │   │   ├── postmortem.py        # esquema + serialización
│   │   │   └── retrieval.py
│   │   ├── safety/
│   │   │   ├── dry_run.py
│   │   │   └── audit_log.py
│   │   └── api/                     # FastAPI + SSE [de Recall]
│   └── tests/
│
├── frontend/                    # React + Vite + TS [de Recall]
│
├── scenarios/
│   ├── seed_incidents.py        # siembra 6-8 postmortems históricos
│   ├── break_schema.py          # rompe el entorno de forma determinista
│   └── scenarios.yaml
│
└── examples/                    # ← EXPLÍCITAMENTE PEDIDO POR LOS JUECES
    ├── 01-schema-drift/
    │   ├── input.txt
    │   ├── timeline.md          # traza completa de la investigación
    │   ├── blast-radius.md
    │   ├── postmortem.md
    │   └── audit-log.json
    ├── 02-cold-vs-warm/         # ★ el mismo incidente sin y con memoria
    └── 03-orphaned-asset/
```

---

## 8. Los tres escenarios de demo

> **Tarea del día 0**: abrir `http://localhost:9002` después de cargar `showcase-ecommerce`, mapear el grafo real y anotar las URNs concretas. Los nombres de abajo son ilustrativos hasta que los confirmes contra el datapack.

### Escenario 1 — Schema drift (el caso base)

Una columna cambia de tipo o se vuelve nullable en una tabla raíz. El agente resuelve el asset, encuentra 12 consumidores aguas abajo incluyendo dos dashboards, rastrea la causa a 2 hops arriba con `get_lineage_paths_between`, taggea lo degradado y guarda el postmortem.

*Demuestra*: recorrido multi-hop + write-back.

### Escenario 2 — Cold vs. warm ★ (el escenario que gana)

**El mismo incidente, corrido dos veces.**

- **Corrida en frío**: memoria vacía. El agente investiga a ciegas, explora tres ramas del linaje, llega a la causa raíz tras 9 llamadas a tools.
- **Corrida en caliente**: la fase 2 recupera el postmortem de la corrida anterior, va directo al ancestro sospechoso, confirma en 3 llamadas.

Poné las dos trazas lado a lado en `examples/02-cold-vs-warm/`. **Es la prueba visual de tu tesis** y ningún otro proyecto va a tener algo así.

### Escenario 3 — Gap de governance (el bonus)

El agente detecta que un asset crítico en el camino del incidente no tiene owner ni domain asignado, y propone `add_owners` + `set_domains` además de las acciones del incidente.

*Demuestra*: que el agente no solo apaga incendios, mejora el catálogo. Es exactamente el pitch comercial de DataHub, dicho por tu proyecto.

---

## 9. Cronograma con criterios de "hecho"

### Domingo 2 — Setup · 3 h

- Arrancar `datahub docker quickstart` **primero**, es lo más lento
- Cargar `showcase-ecommerce` y mapear el grafo a mano en la UI
- **Verificar `TOOLS_IS_MUTATION_ENABLED=true`** y probar un `add_tags` desde Claude Code o Cursor
- Repo creado con `LICENSE` Apache 2.0
- Registro en Devpost + Slack `#agent-hackathon`

> **Hecho cuando**: taggeaste un dataset desde un cliente MCP y lo viste aparecer en la UI de DataHub.

### Lunes 3 — Esqueleto · 4 h

- Portar de Recall la capa LLM y el FastAPI con SSE
- `mcp_client.py` con las tools de lectura
- Fases `intake` + `resolve`

> **Hecho cuando**: le pasás texto libre por consola y devuelve la URN correcta.

### Martes 4 — Impacto · 4 h

- `get_lineage` downstream multi-hop
- Fórmula de scoring implementada
- Agrupación de owners a notificar

> **Hecho cuando**: para un asset conocido devuelve la lista ordenada de consumidores con score, y los números tienen sentido al mirarlos.

### Miércoles 5 — Memoria · 5 h ★

- Esquema de postmortem + `save_document`
- `search_documents` / `grep_documents` en la fase `recall`
- `seed_incidents.py` con 6–8 postmortems históricos plausibles
- Los `investigation_hints` alimentando la fase `root_cause`

> **Hecho cuando**: el escenario cold-vs-warm muestra una diferencia medible en número de llamadas a tools.
> **Este es el día crítico. Si algo se atrasa, que no sea este.**

### Jueves 6 — Causa raíz + write-back · 4 h

- Hipótesis ranqueadas con evidencia citada
- Fases `propose` / `commit` con dry-run, human gate y log de auditoría

> **Hecho cuando**: aprobás un plan por consola y los cambios aparecen en la UI de DataHub.

### Viernes 7 — Frontend · 4 h

- Timeline SSE, grafo de blast radius, panel de incidentes similares, botón de aprobación

> **Hecho cuando**: alguien que no sos vos entiende qué pasó mirando la pantalla.

### Sábado 8 — Escenarios y deploy · 6 h

- Los tres escenarios reproducibles y determinísticos
- `examples/` completa
- Deploy público, o `docker-compose up` de un comando con GIF en el README

> **Hecho cuando**: clonaste el repo en un directorio limpio y funcionó siguiendo solo el README.

### Domingo 9 — Entrega · 5 h

- Video de 3 min grabado, editado y subido **como público**
- README con diagrama de arquitectura y decisiones justificadas
- PR de la Skill open source
- **Submission cargado en Devpost**

> **Hecho cuando**: el submission está cargado. No "casi listo".

### Lunes 10 — Buffer · 2 h

- Repaso con cabeza fresca, ajustes, encuesta de feedback (US$50)
- **Cierre 18:00 ART. Terminá antes del mediodía.**

---

## 10. Mapeo a la rúbrica

Los seis criterios pesan igual. Chequeá que cada uno tenga una respuesta explícita.

| Criterio | Tu respuesta | Dónde lo ve el jurado |
|---|---|---|
| Profundidad de integración | ~12 tools del MCP, lectura **y** mutación, linaje multi-hop, memoria dentro de DataHub | Timeline del demo + sección del README |
| Calidad técnica | Pipeline de fases determinista, toolset separado por fase, dry-run, tests, fallback por SDK | README "Design decisions" + `tests/` |
| Originalidad | El loop de memoria: el sistema mejora con el uso y el conocimiento vive en DataHub | Escenario 2 en el video |
| Aplicabilidad real | On-call de datos, dolor concreto y caro. Experiencia propia detrás | Los primeros 20 segundos del video |
| Calidad de la entrega | Demo hosteado + video + README + `examples/` + GIF | Todo |
| **Bonus open source** | Skill `datahub-incident-triage` publicada en el registry | Link al PR en el submission |

### La contribución open source

Es el ítem más barato de toda la rúbrica y el que menos gente va a hacer. Publicá una Skill en `datahub-project/datahub-skills` siguiendo el formato de las existentes (`datahub-search`, `datahub-lineage`, `datahub-enrich`, `datahub-quality`):

**`datahub-incident-triage`** — la receta para que cualquier agente compatible con Agent Skills haga triage de un incidente de datos: qué tools llamar, en qué orden, cómo interpretar el linaje, cómo escribir el postmortem.

Es la destilación de tu proyecto en un artefacto reutilizable, y es exactamente el tipo de contribución que un mantenedor quiere recibir. Abrí el PR el domingo aunque no esté mergeado — el link al PR alcanza.

---

## 11. Riesgos y planes B

| Riesgo | Señal temprana | Plan B |
|---|---|---|
| Las mutation tools no arrancan | Día 0, el `add_tags` de prueba falla | Escribir vía SDK de Python (`acryl-datahub`). Sigue calificando |
| El linaje del datapack es más chato de lo esperado | Día 0, mirando el grafo en la UI | Ingestar linaje sintético extra con el SDK, o cambiar a otro datapack |
| Las respuestas de linaje se truncan | Día 2, contexto lleno | Subir `TOOL_RESPONSE_TOKEN_LIMIT`, paginar el recorrido |
| `search_documents` no recupera bien | Día 3, la fase recall trae basura | Activar `SEMANTIC_SEARCH_ENABLED=true`; si no alcanza, índice propio |
| El frontend come el fin de semana | Viernes a la noche sin timeline | Cortarlo. Un CLI con salida rica califica igual |
| El demo hosteado no sale | Sábado | `docker-compose up` + GIF en el README. Documentado desde ya |
| El video sale largo o confuso | Domingo | Guión escrito **antes** de grabar, con cronómetro por sección |

### Mínimo entregable vs. ideal

Definí esto ahora, en frío, para no negociarlo con vos mismo el domingo a las 2 de la mañana:

**Mínimo viable** (esto se entrega sí o sí): CLI que hace las 8 fases, escribe de vuelta a DataHub con aprobación, el escenario 2 cold-vs-warm funcionando, `examples/`, README, video.

**Ideal**: todo lo anterior + frontend con timeline y grafo + demo hosteado + los tres escenarios + PR de la Skill.

El mínimo viable ya es un proyecto competitivo. Todo lo demás es margen.

---

## 12. Los primeros tres comandos

```bash
# 1. Esto tarda. Arrancalo ya y seguí con lo demás mientras baja.
pip install acryl-datahub && datahub docker quickstart

# 2. Datos con linaje real para jugar
datahub init --username datahub --password datahub
datahub datapack load showcase-ecommerce

# 3. El repo, con la licencia correcta desde el commit uno
mkdir hindsight && cd hindsight && git init
curl -sL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
```

Después: abrí `http://localhost:9002`, buscá un dataset con varios consumidores aguas abajo, y anotá su URN. Ese va a ser el protagonista de tu demo.

---

## Enlaces

**Hackathon** — [Devpost](https://datahub.devpost.com/) · [Reglas](https://datahub.devpost.com/rules) · [Recursos](https://datahub.devpost.com/resources) · [Blog del anuncio](https://datahub.com/blog/build-with-datahub-agent-hackathon/) · Slack `#agent-hackathon`

**Docs** — [Quickstart](https://docs.datahub.com/docs/quickstart) · [MCP Server](https://docs.datahub.com/docs/features/feature-guides/mcp) · [Agent Context Kit](https://docs.datahub.com/docs/dev-guides/agent-context/agent-context) · [Analytics Agent](https://docs.datahub.com/docs/features/feature-guides/analytics-agent) · [Autonomous Data Agents](https://datahub.com/blog/building-autonomous-data-agents/) · [Skills Registry](https://datahub.com/blog/datahub-open-source-skills-registry/)

**Repos** — [DataHub Core](https://github.com/datahub-project/datahub) · [Skills](https://github.com/datahub-project/datahub-skills) · [Analytics Agent](https://github.com/datahub-project/analytics-agent) · [MCP Server](https://github.com/acryldata/mcp-server-datahub)
