"""cli.py - Interfaz de linea de comandos del simplificador logico.

Ejemplos:
  python cli.py caso 1                       # reproduce un caso obligatorio (1..7, 8a, 8b)
  python cli.py casos                        # lista los casos
  python cli.py minimizar -n 4 --m 1,3,7,11,15 --d 0,2,5 --kmap fig.png
  python cli.py minimizar -n 4 --M 0,1,2 --d 15
  python cli.py expr "A'B'C + A'BC + AB'C'" --traza
  python cli.py benchmark                    # benchmark empirico n=2..6
"""
import argparse, json, sys
from simplificador.parser_boole import desde_listas, desde_expresion, parsear_expresion, a_str
from simplificador.quine_mccluskey import minimizar_sop, minimizar_pos, expresion_pos, cubo_a_producto
from simplificador.algebra_boole import simplificar_algebraicamente
from simplificador.kmap_visualizer import kmap_ascii, figura_kmap
from simplificador.validador_benchmark import (casos_obligatorios, ejecutar_caso, validar, benchmark, ast_canonica, costo_ast)


def _enteros(txt):
    return [int(x) for x in txt.replace(" ", "").split(",") if x != ""] if txt else []


def _reportar(f, traza=False, kmap=None):
    n = f.n
    unos, dc = set(f.minterminos), set(f.indiferentes)
    print(f"n = {n}   ∑m{sorted(unos)}   ∑d{sorted(dc)}")
    if n <= 4:
        print(kmap_ascii(n, unos, dc))
    rs, rp = minimizar_sop(n, unos, dc), minimizar_pos(n, unos, dc)
    print("Implicantes primos :", [cubo_a_producto(p, n) for p in rs.primos])
    print("Primos esenciales  :", [cubo_a_producto(p, n) for p in rs.esenciales])
    print("Método de cobertura:", rs.metodo, f"(soluciones mínimas empatadas: {len(rs.soluciones_minimas)})")
    sop, pos = rs.expresion_sop(), expresion_pos(rp)
    print("SOP mínima         :", sop)
    print("POS mínima         :", pos)
    v1, v2 = validar(f, sop), validar(f, pos)
    print(f"Validación 2^n     : SOP {v1['coinciden']}/{v1['filas']}  POS {v2['coinciden']}/{v2['filas']}")
    c0, c1 = costo_ast(ast_canonica(f)), costo_ast(parsear_expresion(sop))
    print(f"Literales {c0['literales']} → {c1['literales']}   Compuertas {c0['compuertas']} → {c1['compuertas']}")
    if traza:
        terms, tr = simplificar_algebraicamente(ast=f.ast) if f.ast is not None else simplificar_algebraicamente(n=n, minterminos=unos)
        print("\nTraza algebraica:")
        for p in tr:
            print(f"  {p.n:>2}. [{p.ley}] {p.detalle}\n      → {p.expresion}")
    if kmap:
        if n > 4:
            print("K-Map visual solo disponible para n <= 4")
        else:
            figura_kmap(kmap, n, unos, dc, rs.cobertura, sop, "K-Map generado por cli.py")
            print("K-Map guardado en", kmap)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Simplificador lógico: álgebra de Boole, Quine-McCluskey/Petrick y K-Map")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("casos", help="lista los casos obligatorios")
    c = sp.add_parser("caso", help="ejecuta un caso obligatorio"); c.add_argument("id"); c.add_argument("--traza", action="store_true")
    c.add_argument("--kmap")
    m = sp.add_parser("minimizar", help="minimiza desde minterminos/maxterminos")
    m.add_argument("-n", type=int, required=True); m.add_argument("--m", default=""); m.add_argument("--M", default=None)
    m.add_argument("--d", default=""); m.add_argument("--traza", action="store_true"); m.add_argument("--kmap")
    e = sp.add_parser("expr", help="minimiza una expresión simbólica"); e.add_argument("texto"); e.add_argument("-n", type=int)
    e.add_argument("--traza", action="store_true"); e.add_argument("--kmap")
    sp.add_parser("benchmark", help="benchmark empírico n=2..6")
    a = ap.parse_args(argv)
    if a.cmd == "casos":
        for k in casos_obligatorios():
            print(f"{k.id:>2}  {k.nombre:<34} n={k.f.n}  {k.nota}")
    elif a.cmd == "caso":
        k = {x.id: x for x in casos_obligatorios()}.get(a.id)
        if not k:
            sys.exit("Caso inexistente. Use: python cli.py casos")
        print(f"=== Caso {k.id}: {k.nombre} ===")
        _reportar(k.f, a.traza, a.kmap)
    elif a.cmd == "minimizar":
        f = desde_listas(a.n, _enteros(a.m), _enteros(a.d), _enteros(a.M) if a.M is not None else None)
        _reportar(f, a.traza, a.kmap)
    elif a.cmd == "expr":
        _reportar(desde_expresion(a.texto, a.n), a.traza, a.kmap)
    elif a.cmd == "benchmark":
        for r in benchmark():
            print(r)


if __name__ == "__main__":
    main()
