# Simplificador lógico con álgebra de Boole y mapas de Karnaugh

**Universidad Peruana Cayetano Heredia (UPCH) · Facultad de Ciencias e Ingeniería · Ingeniería Informática**
**Estructuras Discretas II (Sección G01 – 2026-II) · Grupo 06 – Tema 06**
Asesor: Dr. Ing. CIP. Omar Felix Illesca Cangalaya

Autores (orden alfabético): Bances Panaque, Jose Junior · Jimenez Ostos, Giacomo Renato · Ramirez Uriol, Ruben Moises Enmanuel · Romero Meza, Piero Cemei · Uscamayta Lazaro, Marx Stiven.

Herramienta de línea de comandos y biblioteca Python para simplificar funciones booleanas de 2 a 6 variables:

| Módulo | Función |
|---|---|
| `simplificador/parser_boole.py` | Entrada `∑m`, `∏M`, `∑d` y expresiones simbólicas (`A'B'C + A'BC`), AST y evaluación |
| `simplificador/algebra_boole.py` | Simplificación algebraica paso a paso con la ley aplicada en cada paso |
| `simplificador/quine_mccluskey.py` | Primos implicantes, esenciales, Petrick, SOP y POS mínimas (con indiferentes) |
| `simplificador/kmap_visualizer.py` | K-Map de 2, 3 y 4 variables (Gray, adyacencia toroidal) y PNG a 300 dpi |
| `simplificador/validador_benchmark.py` | Validación exhaustiva `2ⁿ`, métricas de literales/compuertas, benchmark |
| `cli.py` | Interfaz de línea de comandos |
| `ejecutar_todo.py` | Reproduce todos los resultados y figuras del informe |
| `tests/test_simplificador.py` | 30 pruebas automatizadas (`unittest`) |

## Requisitos
- Python ≥ 3.9
- Núcleo (parser, álgebra, Quine-McCluskey, validación y benchmark): **solo biblioteca estándar**.
- `matplotlib` únicamente para dibujar K-Maps y figuras: `pip install -r requirements.txt`

## Instalación
```bash
git clone [INSERTAR URL DEL REPOSITORIO GITHUB]
cd Proyecto_Grupo06_Simplificador_Boole_KMap
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución
```bash
python -m unittest -v tests.test_simplificador         # pruebas (30)
python ejecutar_todo.py                                # casos + benchmark + 6 figuras + JSON/CSV en resultados/
python cli.py casos                                    # lista los casos obligatorios
python cli.py caso 1 --traza                           # caso 3 variables con traza algebraica
python cli.py caso 2 --kmap kmap_toroidal.png          # caso toroidal + PNG
python cli.py minimizar -n 4 --m 1,3,7,11,15 --d 0,2,5 # con indiferentes
python cli.py minimizar -n 3 --M 0,1 --d 7             # desde maxterminos
python cli.py expr "A'B'C + A'BC + AB'C'" --traza      # expresión simbólica
python cli.py benchmark                                # benchmark n=2..6
```

## Ejemplo de salida (`python cli.py caso 7`)
```
=== Caso 7: Límite: cobertura cíclica ===
Primos esenciales  : []
Método de cobertura: Petrick (soluciones mínimas empatadas: 2)
SOP mínima         : A'B' + AC + BC'
```

## Estructura
```
Proyecto_Grupo06_Simplificador_Boole_KMap/
├── simplificador/   (módulos)      ├── tests/      (pruebas)
├── figuras/         (PNG 300 dpi)  ├── resultados/ (JSON, CSV, logs reales)
├── docs/            (notas)        ├── cli.py · ejecutar_todo.py
└── README.md · BITACORA_Y_REPARTO_GITHUB.md · requirements.txt
```

## Convenciones
`A` es la variable más significativa; `X'` es el complemento; la yuxtaposición es AND; `+` es OR; `⊕`/`^` es XOR.
Costo de compuertas: AND/OR de *k* entradas (k ≥ 2) cuenta 1; NOT = inversores distintos de variables (compartidos).

## Atribución de código e integridad académica
Los algoritmos (parser, motor algebraico, Quine-McCluskey, Petrick, visualizador, validación y benchmark) se implementaron específicamente
para este trabajo a partir de las definiciones de la bibliografía del informe; no se reutilizó código de terceros. El diseño y el código se
elaboraron con asistencia de una herramienta de inteligencia artificial (Claude, de Anthropic); el equipo revisó, ejecutó y se responsabiliza del contenido.
Se usan la biblioteca estándar de Python y `matplotlib` (solo visualización). Las salidas y tiempos reportados provienen de ejecuciones reales (`resultados/`).

## Licencia
Uso académico (UPCH, 2026-II).
