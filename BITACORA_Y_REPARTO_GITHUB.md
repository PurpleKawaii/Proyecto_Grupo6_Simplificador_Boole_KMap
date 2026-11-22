# Bitácora y reparto de trabajo en GitHub — Grupo 06 (Tema 06)

Repositorio: `[INSERTAR URL DEL REPOSITORIO GITHUB]`

## 1. Reparto equilibrado de módulos y ramas

| Integrante | Rama | Módulos / entregables | Commits sugeridos |
|---|---|---|---|
| Bances Panaque, Jose Junior | `feature/parser-algebra` | `parser_boole.py`, `algebra_boole.py` | 4 |
| Jimenez Ostos, Giacomo Renato | `feature/quine-petrick` | `quine_mccluskey.py` | 4 |
| Ramirez Uriol, Ruben Moises Enmanuel | `feature/kmap-visual` | `kmap_visualizer.py`, figuras 2–4 | 4 |
| Romero Meza, Piero Cemei | `feature/validacion-benchmark` | `validador_benchmark.py`, figuras 5–6, `ejecutar_todo.py` | 4 |
| Uscamayta Lazaro, Marx Stiven | `feature/cli-tests-docs` | `cli.py`, `tests/`, `README.md`, figura 1 | 4 |

Flujo: cada integrante crea su rama desde `main`, abre un *Pull Request* y otro integrante lo revisa (revisión cruzada en anillo:
Bances→Jimenez→Ramirez→Romero→Uscamayta→Bances). Se fusiona con *squash* o *merge* manteniendo el historial.

## 2. Mensajes de commit sugeridos

**Bances** — `feature/parser-algebra`
1. `feat(parser): tokenizador y gramática de expresiones booleanas (AND implícito, ', ⊕)`
2. `feat(parser): modo ∑m/∏M/∑d con validación de rangos`
3. `feat(algebra): reescritura a SOP (De Morgan, doble negación, distributiva)`
4. `feat(algebra): adyacencia, absorción y consenso con traza de leyes`

**Jimenez** — `feature/quine-petrick`
1. `feat(qm): tabulación y primos implicantes (valor, máscara)`
2. `feat(qm): primos esenciales y cobertura con indiferentes`
3. `feat(qm): método de Petrick con absorción y dominancia`
4. `feat(qm): POS por dualidad y respaldo exacto por ramificación y acotamiento`

**Ramirez** — `feature/kmap-visual`
1. `feat(kmap): disposición Gray 2, 3 y 4 variables`
2. `feat(kmap): agrupamientos toroidales (bordes y esquinas)`
3. `feat(kmap): exportación PNG 300 dpi con leyenda`
4. `docs(figuras): figuras 2, 3 y 4 del informe`

**Romero** — `feature/validacion-benchmark`
1. `feat(validador): equivalencia exhaustiva 2^n por re-parseo`
2. `feat(validador): métricas de literales y compuertas`
3. `feat(benchmark): n=2..6, instancias aleatorias y peor caso`
4. `docs(figuras): figuras 5 y 6 y script ejecutar_todo.py`

**Uscamayta** — `feature/cli-tests-docs`
1. `feat(cli): subcomandos caso, minimizar, expr, benchmark`
2. `test: suite unittest (30 pruebas) con casos límite`
3. `docs: README, requisitos y guía de ejecución`
4. `docs(figuras): figura 1 de arquitectura`

## 3. Registro verificable (completar tras subir a GitHub)

| Integrante | Rama | Commit | Hash | Fecha | PR revisado |
|---|---|---|---|---|---|
| Bances | feature/parser-algebra | 1–4 | `[INSERTAR HASH DE COMMIT / FECHA]` | | |
| Jimenez | feature/quine-petrick | 1–4 | `[INSERTAR HASH DE COMMIT / FECHA]` | | |
| Ramirez | feature/kmap-visual | 1–4 | `[INSERTAR HASH DE COMMIT / FECHA]` | | |
| Romero | feature/validacion-benchmark | 1–4 | `[INSERTAR HASH DE COMMIT / FECHA]` | | |
| Uscamayta | feature/cli-tests-docs | 1–4 | `[INSERTAR HASH DE COMMIT / FECHA]` | | |

Verificación: `git shortlog -sn --all` y `git log --graph --oneline --all` deben mostrar 4 commits por integrante.
