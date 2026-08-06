# Cómo publicar la skill en `datahub-project/datahub-skills`

Guía para llevar `skills/datahub-incident-triage/` al repo open source de DataHub y abrir el PR. **Nada de esto está ejecutado**: la skill vive en este repo y esto es el instructivo para publicarla cuando quieras.

Para el hackathon **alcanza con el link del PR** — no hace falta que lo mergeen.

---

## 1. Qué es un fork y por qué hace falta

No tenés permiso de escritura sobre `datahub-project/datahub-skills`, así que no podés crear una branch ahí. Un fork es una copia del repo bajo tu propia cuenta (`github.com/<vos>/datahub-skills`) sobre la que sí escribís. GitHub recuerda de dónde salió, y por eso después te ofrece abrir un PR desde tu copia hacia el original.

Es una acción **pública**: el fork aparece en tu perfil y en la lista de forks del repo original. No expone nada privado tuyo.

Se deshace: el fork se borra desde Settings del repo, y el PR se cierra con `gh pr close`. Nada es irreversible.

---

## 2. Los comandos

```bash
cd ~/Documents                                       # fuera de hindsight/, para no anidar repos git
gh repo fork datahub-project/datahub-skills --clone  # crea tu copia y la baja a disco
cd datahub-skills
git checkout -b feat/incident-triage-skill

cp -r ~/Documents/hindsight/skills/datahub-incident-triage skills/
# + los archivos de la sección 3

pre-commit run --all-files                           # el gate de la CI, antes de pushear
git add . && git commit -m "feat: add datahub-incident-triage skill"
git push -u origin feat/incident-triage-skill
gh pr create --repo datahub-project/datahub-skills --title "feat: add datahub-incident-triage skill"
```

El clon queda con dos remotos: `origin` es tu fork (escribís ahí) y `upstream` es el repo de DataHub (solo lectura). Nada de esto toca `hindsight/`: son repos separados.

---

## 3. Qué archivos tocar en el fork

### Crear

| Archivo                               | Qué es                                                                                                                                                  |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skills/datahub-incident-triage/`     | Copia tal cual desde Hindsight                                                                                                                          |
| `commands/catalog-incident-triage.md` | Wrapper de slash command. Copiá `commands/catalog-lineage.md` y adaptalo. Ojo la asimetría del repo: el comando es `catalog-*`, la skill es `datahub-*` |

Estructura del wrapper de comando:

```markdown
---
name: catalog-incident-triage
description: Triage a data incident — blast radius, root cause, and write-back
argument-hint: "[incident report or affected asset]"
---

# DataHub Incident Triage

Use the Skill tool to invoke the full `datahub-incident-triage` skill:

    Skill tool:
      skill: "datahub-skills:datahub-incident-triage"

**User's request:** $ARGUMENTS

...
```

### Modificar

| Archivo                                                        | Qué cambiar                                                                                                                                                                                                                                                                     |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skills/using-datahub/SKILL.md`                                | La routing table que se inyecta al inicio de sesión. Dice "5 DataHub catalog interaction skills" → pasa a 6. Fila en `## Skill Routing Table`, entrada en `## Disambiguation Rules`, ejemplo en `## CLI Attribution`                                                            |
| `skills/datahub-quality/SKILL.md` y `datahub-lineage/SKILL.md` | Fila recíproca en su tabla `## Not This Skill`. La convención del repo es que toda skill lista a las demás                                                                                                                                                                      |
| `README.md` raíz                                               | ~5 puntos de inserción: párrafo intro, `#### Incident triage` bajo "Catalog interaction skills", fila en la tabla "What works where", fila en la tabla de comandos, y las menciones sueltas (`cp -r` de "Manual install", árbol de "Repo layout", lista de "Where things live") |

**`skills/using-datahub/SKILL.md` es lo que un mantenedor va a mirar primero.** `datahub-quality` ya se queda con "raise incident / resolve incident / active incidents", así que la frontera tiene que estar declarada con precisión y de los dos lados. La regla de una línea:

> Quality **registra y gestiona** el incidente (lo levanta, lo resuelve, crea las assertions que lo detectan). Incident-triage **lo investiga**: recorre el grafo para saber a quién afecta y qué lo causó, y escribe el diagnóstico de vuelta. Se componen — un triage puede terminar levantando un incidente formal con quality.

### No tocar

- `.claude-plugin/plugin.json` y `.claude-plugin/marketplace.json` — no enumeran skills individualmente. El plugin empaqueta el repo entero (`"source": "./"`) y las skills se autodescubren desde `skills/*/SKILL.md`. Además el `version` lo maneja release-please y el CONTRIBUTING prohíbe editarlo a mano.
- `CHANGELOG.md` y `.release-please-manifest.json` — auto-generados.
- `evaluations/` y `tests/` — solo existen para las skills de connector. Ninguna skill de catálogo (search, enrich, lineage, quality, setup) los tiene.

---

## 4. El lint que hay que pasar

La CI corre `pre-commit`, que incluye prettier y markdownlint-cli2:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

**Prettier realinea las tablas markdown.** Si el archivo no viene ya formateado, el hook lo modifica y la CI falla. Corré `pre-commit run --all-files` antes de pushear, siempre.

Reglas efectivas del repo:

- Largo de línea libre (`MD013` off, `proseWrap: preserve`). No re-wrapees prosa.
- Headings ATX (`#`), con línea en blanco antes y después.
- Bullets con `-`, indent de 2 espacios.
- Nunca dos líneas en blanco seguidas (`MD012`).
- EOL `lf`, un solo `\n` al final, sin trailing whitespace.
- Permitido: HTML inline `<!-- -->`, headings duplicados, headings con `?`, `**bold**` como pseudo-heading.

---

## 5. El PR

- **Título**: `feat: add datahub-incident-triage skill`. Conventional Commits, **validado por CI** (`amannn/action-semantic-pull-request`). Minúscula después de `feat:` — si ponés mayúscula lo rechaza. El título se convierte en el commit al hacer squash-merge, y `feat:` dispara un minor bump vía release-please.
- **Branch**: no hay convención documentada ni validada. `feat/incident-triage-skill` está bien.
- **Cuerpo**: qué resuelve, por qué no se solapa con `datahub-quality`, y link a Hindsight como implementación de referencia — con la métrica de `examples/02-cold-vs-warm/` (29 llamadas en frío vs. 17 en caliente) como evidencia de que el loop de memoria funciona contra un DataHub real.
- No hay PR template ni checklist.
- Checks de CI: `Lint` (pre-commit) y `Lint PR Title`.

---

## 6. Para el submission de Devpost

El link del PR va en el campo de contribución open source. Si el PR todavía no está abierto el día de la entrega, sirve el link al directorio `skills/datahub-incident-triage/` de este repo — pero el PR es lo que cuenta para el bonus de la rúbrica.
