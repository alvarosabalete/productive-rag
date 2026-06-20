---
name: spec-driven-development
description: >-
  Flujo ligero de Spec Driven Development. Antes de implementar una feature
  nueva no trivial, redacta un spec breve en specs/ y ESPERA la aprobación del
  usuario antes de escribir código. Úsala siempre que el usuario pida construir,
  añadir, implementar o diseñar una funcionalidad, endpoint, módulo, servicio o
  fase del roadmap que no sea un fix trivial — aunque no mencione "spec" ni
  "diseño" explícitamente. Úsala también cuando vaya a tomarse una decisión
  arquitectónica costosa de revertir (elección de tecnología, patrón estructural,
  trade-off de seguridad o concurrencia), para registrarla como ADR. No la uses
  para fixes de una línea, cambios triviales, renombrados, o cuando el usuario
  pida explícitamente "hazlo directo, sin spec".
---

# Spec Driven Development (ligero)

Diseña antes de construir. La idea: para cualquier feature de cierto tamaño,
primero acordamos **qué** se va a hacer y **cómo**, en un documento corto, y solo
después se escribe código. Esto evita el patrón caro de implementar rápido algo
mal entendido y tener que rehacerlo.

El énfasis es en **ligero**: el spec es una herramienta para pensar y alinear, no
burocracia. Si te descubres rellenando secciones por rellenarlas, el spec es
demasiado largo. Mejor medio folio claro que tres folios de relleno.

## Cuándo aplica (y cuándo no)

Aplica cuando vas a construir algo no trivial: un endpoint nuevo, un módulo, un
servicio, integrar una librería, una fase del roadmap. La señal es que hay
**decisiones que tomar** (estructura, contratos, trade-offs) y más de un camino
razonable.

NO apliques el flujo para fixes de una línea, ajustes de config, renombrados,
correcciones obvias de bugs, o si el usuario dice explícitamente que quiere ir
directo. En la duda sobre si algo es "trivial", pregunta en una frase en vez de
imponer el proceso.

## El flujo

```
1. Aclarar   → si hay ambigüedad real, pregunta antes de escribir el spec
2. Redactar  → spec corto en specs/<slug>.md
3. ¿ADR?     → si hay una decisión arquitectónica de peso, propón un ADR
4. GATE      → presenta el spec, PARA, espera el OK del usuario
5. Construir → implementa contra el spec aprobado
6. Cerrar    → si la implementación se desvió, actualiza el spec
```

### 1. Aclarar

Antes de redactar, identifica los huecos que de verdad cambian el diseño
(formato de datos, contratos de API, comportamiento esperado, restricciones).
Si los hay, pregunta de forma concreta y breve. No inventes requisitos para
rellenar; un spec construido sobre suposiciones erróneas es peor que ninguno.

Si no hay ambigüedad real, salta directo a redactar.

### 2. Redactar el spec

Crea `specs/<slug>.md` con un nombre descriptivo en kebab-case. Si la feature
mapea a una fase del roadmap (F1–F5 en `CLAUDE.md`), prefija con la fase para que
sea fácil de localizar: p. ej. `specs/f2-rag-core.md`, `specs/f3-auth-jwt.md`.

Usa esta plantilla. Omite secciones que no apliquen en vez de rellenarlas en
vacío:

```markdown
# <Título de la feature>

## Objetivo
Qué problema resuelve y por qué ahora. 1–3 frases.

## Alcance
- **Incluye:** lo que sí entra.
- **No incluye:** lo que queda fuera (evita malentendidos y scope creep).

## Enfoque técnico
Cómo se va a construir: componentes que se tocan, contratos/firmas relevantes,
flujo de datos, librerías. Lo justo para que alguien entienda el plan sin leer el
código. Bullets > prosa.

## Criterios de aceptación
Lista verificable de cuándo está "hecho". Cada punto debe ser comprobable
(idealmente un test o una comprobación manual concreta).
- [ ] ...
- [ ] ...

## Decisiones abiertas (opcional)
Dudas que hay que resolver antes o durante. Bórralas cuando se cierren.
```

Mantén el spec proporcionado al tamaño de la feature. Una feature pequeña puede
caber en 15 líneas; eso es éxito, no falta de rigor.

### 3. ¿Hace falta un ADR?

Un ADR (Architecture Decision Record) documenta **una decisión arquitectónica
costosa de revertir** y el porqué: elección de tecnología, un patrón estructural,
un trade-off de seguridad o concurrencia. La mayoría de specs NO necesitan ADR;
los ADRs valen precisamente porque son raros y selectivos. Si abusas, se llenan
de ruido y pierden valor.

Propón un ADR solo cuando la decisión:
- afecta a la arquitectura más allá de esta feature, y
- sería cara o disruptiva de cambiar después, y
- alguien en el futuro se preguntará legítimamente "¿por qué se hizo así?".

Si procede, créalo en `docs/adr/NNNN-<slug>.md` (numeración incremental de 4
dígitos: `0001`, `0002`, …) con esta plantilla MADR-lite:

```markdown
# NNNN. <Título de la decisión>

- Estado: aceptada
- Fecha: <YYYY-MM-DD>

## Contexto
La situación y las fuerzas en juego que obligan a decidir.

## Decisión
Lo que se decide, en voz activa: "Usaremos X".

## Alternativas consideradas
- **X (elegida):** por qué.
- **Y:** por qué no.

## Consecuencias
Lo que se gana y lo que se acepta como coste (positivas y negativas).
```

Nota para este repo: en `CLAUDE.md` ya viven "decisiones cerradas". Si una de
ellas reaparece y merece contexto completo, ese es buen material para un ADR.

### 4. GATE de aprobación — esto es la esencia de SDD

Tras escribir el spec (y el ADR si aplica), **detente y NO escribas código de
producción todavía**. Presenta un resumen breve al usuario y pide aprobación
explícita. Algo como: "He dejado el spec en `specs/<slug>.md`. ¿Lo apruebas o
quieres cambios antes de implementar?".

Esperar aquí es lo que da valor al método: es barato corregir el rumbo en el spec
y caro corregirlo en el código. Si el usuario pide cambios, edita el spec y
vuelve a preguntar. No cruces el gate por iniciativa propia.

### 5. Construir

Con el OK, implementa contra el spec. Trátalo como la fuente de verdad de esta
feature: los criterios de aceptación son tu checklist de "hecho".

### 6. Cerrar

Si durante la implementación el diseño se desvió del spec (pasa, y está bien),
actualiza el spec para que refleje lo construido. Un spec que miente es peor que
no tenerlo. Esto es rápido y mantiene `specs/` como documentación viva fiable.

## Principios

- **Ligero de verdad:** el spec sirve para pensar y alinear, no para cumplir un
  expediente. Si no aporta claridad, sóbralo.
- **El gate no es opcional:** redactar el spec y seguir codeando sin esperar el
  OK rompe el método. La pausa es el punto.
- **ADR con moderación:** raro y selectivo. Mejor cero ADRs que ADRs de relleno.
- **Idioma:** specs, ADRs y mensajes en español, acorde al proyecto.
