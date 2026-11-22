"""validador_benchmark.py
Validacion formal exhaustiva (2^n filas), metricas de costo y benchmark empirico.
Autoria propia; solo biblioteca estandar (+ random/statistics/time).
"""
import random
import statistics
import time
from dataclasses import dataclass, field
from .parser_boole import (FuncionBooleana, desde_listas, desde_expresion, parsear_expresion,
                           evaluar, asignacion, a_str, NOMBRES)
from .quine_mccluskey import (minimizar_sop, minimizar_pos, expresion_pos, cubo_a_producto, cubo_a_suma,
                              primos_implicantes, literales)
from .algebra_boole import simplificar_algebraicamente


# ------------------------------------------------------------------ costos
def _expandir_xor(a):
    k = a[0]
    if k == "xor":
        x, y = _expandir_xor(a[1]), _expandir_xor(a[2])
        return ("or", [("and", [x, ("not", y)]), ("and", [("not", x), y])])
    if k == "not":
        return ("not", _expandir_xor(a[1]))
    if k in ("and", "or"):
        return (k, [_expandir_xor(h) for h in a[1]])
    return a


def costo_ast(ast):
    """Devuelve dict(literales, terminos, and_, or_, not_, compuertas).
    Convencion: compuertas AND/OR de n entradas (n>=2) cuentan 1; NOT = inversores distintos
    sobre variables (compartidos) + NOT sobre subexpresiones."""
    ast = _expandir_xor(ast)
    lit = [0]
    and_ = [0]
    or_ = [0]
    not_sub = [0]
    inv = set()

    def rec(a):
        k = a[0]
        if k == "var":
            lit[0] += 1
        elif k == "const":
            pass
        elif k == "not":
            h = a[1]
            if h[0] == "var":
                lit[0] += 1
                inv.add(h[1])
            else:
                not_sub[0] += 1
                rec(h)
        elif k in ("and", "or"):
            if len(a[1]) >= 2:
                (and_ if k == "and" else or_)[0] += 1
            for h in a[1]:
                rec(h)
    rec(ast)
    if ast[0] == "or":
        terminos = len(ast[1])
    elif ast[0] == "and" and all(h[0] == "or" for h in ast[1]):
        terminos = len(ast[1])
    else:
        terminos = 0 if ast[0] == "const" else 1
    n_not = len(inv) + not_sub[0]
    return {"literales": lit[0], "terminos": terminos, "and": and_[0], "or": or_[0], "not": n_not,
            "compuertas": and_[0] + or_[0] + n_not}


def _prod_ast(lits):
    return lits[0] if len(lits) == 1 else ("and", lits)


def _sum_ast(lits):
    return lits[0] if len(lits) == 1 else ("or", lits)


def _lit(j, pol):
    v = ("var", NOMBRES[j])
    return v if pol else ("not", v)


def ast_sop_desde_cubos(cubos, n):
    if not cubos:
        return ("const", 0)
    ts = []
    for v, k in cubos:
        lits = [_lit(j, (v >> (n - 1 - j)) & 1) for j in range(n) if not (k >> (n - 1 - j)) & 1]
        if not lits:
            return ("const", 1)
        ts.append(_prod_ast(lits))
    return ts[0] if len(ts) == 1 else ("or", ts)


def ast_pos_desde_cubos_complemento(cubos, n):
    """cubos de f' -> POS de f."""
    if not cubos:
        return ("const", 1)
    cs = []
    for v, k in cubos:
        lits = [_lit(j, not ((v >> (n - 1 - j)) & 1)) for j in range(n) if not (k >> (n - 1 - j)) & 1]
        if not lits:
            return ("const", 0)
        cs.append(_sum_ast(lits))
    return cs[0] if len(cs) == 1 else ("and", cs)


def ast_canonica(f):
    n = f.n
    if f.forma_original == "expr":
        return f.ast
    if f.forma_original == "pos":
        ceros = sorted(f.maxterminos)
        if not ceros:
            return ("const", 1)
        cs = []
        for m in ceros:
            cs.append(_sum_ast([_lit(j, not ((m >> (n - 1 - j)) & 1)) for j in range(n)]))
        return cs[0] if len(cs) == 1 else ("and", cs)
    ms = sorted(f.minterminos)
    if not ms:
        return ("const", 0)
    ts = [_prod_ast([_lit(j, (m >> (n - 1 - j)) & 1) for j in range(n)]) for m in ms]
    return ts[0] if len(ts) == 1 else ("or", ts)


# ------------------------------------------------------------- validacion
def validar(f: FuncionBooleana, texto_simplificado):
    """Re-parsea la cadena simplificada (independiente del minimizador) y la compara con f en las
    2^n filas. Los indiferentes no cuentan como discrepancia. Devuelve dict."""
    ast = parsear_expresion(texto_simplificado)
    desc, ok_filas = [], 0
    for i in range(2 ** f.n):
        v = evaluar(ast, asignacion(i, f.n))
        if i in f.indiferentes:
            ok_filas += 1
            continue
        esp = 1 if i in f.minterminos else 0
        if v == esp:
            ok_filas += 1
        else:
            desc.append(i)
    return {"filas": 2 ** f.n, "coinciden": ok_filas, "discrepancias": desc, "equivalente": not desc}


def equivalencia_ast(a, b, n):
    return all(evaluar(a, asignacion(i, n)) == evaluar(b, asignacion(i, n)) for i in range(2 ** n))


# ------------------------------------------------------------------ casos
@dataclass
class Caso:
    id: str
    nombre: str
    f: FuncionBooleana
    nota: str = ""


def casos_obligatorios():
    rnd5 = random.Random(5)
    rnd6 = random.Random(6)
    m5 = sorted(i for i in range(32) if rnd5.random() < 0.5)
    m6 = sorted(i for i in range(64) if rnd6.random() < 0.5)
    return [
        Caso("1", "Normal, 3 variables", desde_expresion("A'B'C + A'BC + AB'C + ABC' + ABC", 3),
             "Reducción clara con traza algebraica completa"),
        Caso("2", "Normal, 4 variables toroidal", desde_listas(4, [0, 2, 5, 7, 8, 10, 13, 15], descripcion="∑m(0,2,5,7,8,10,13,15)"),
             "Agrupamiento de las 4 esquinas envolventes"),
        Caso("3", "4 variables con indiferentes", desde_listas(4, [1, 3, 7, 11, 15], [0, 2, 5], descripcion="∑m(1,3,7,11,15) + ∑d(0,2,5)"),
             "Reducción adicional gracias a X"),
        Caso("4", "Límite: tautología", desde_listas(3, range(8), descripcion="∑m(0,…,7)"), "Todos 1 → 1"),
        Caso("5", "Límite: contradicción", desde_listas(3, maxterminos=range(8), descripcion="∏M(0,…,7)"), "Todos 0 → 0"),
        Caso("6", "Límite: paridad XOR 4 var", desde_listas(4, [1, 2, 4, 7, 8, 11, 13, 14], descripcion="∑m(1,2,4,7,8,11,13,14)"),
             "Tablero de ajedrez; irreducible"),
        Caso("7", "Límite: cobertura cíclica", desde_listas(3, [0, 1, 2, 5, 6, 7], descripcion="∑m(0,1,2,5,6,7)"),
             "Sin primos esenciales; requiere Petrick"),
        Caso("8a", "Escalabilidad: 5 variables", desde_listas(5, m5, descripcion="∑m aleatorio (semilla 5, p=0,5)"),
             "Fuera del alcance visual del K-Map plano"),
        Caso("8b", "Escalabilidad: 6 variables", desde_listas(6, m6, descripcion="∑m aleatorio (semilla 6, p=0,5)"),
             "Fuera del alcance visual del K-Map plano"),
    ]


def _tiempo_ms(fn, reps):
    t0 = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t0) / reps * 1000.0


def ejecutar_caso(caso: Caso, reps=None):
    f = caso.f
    n = f.n
    unos, dc = set(f.minterminos), set(f.indiferentes)
    reps = reps or (30 if n <= 4 else 5)
    rs = minimizar_sop(n, unos, dc)
    rp = minimizar_pos(n, unos, dc)
    sop = rs.expresion_sop()
    pos = expresion_pos(rp)
    t_ms = _tiempo_ms(lambda: (minimizar_sop(n, unos, dc), minimizar_pos(n, unos, dc)), reps)
    orig_ast = ast_canonica(f)
    c_orig = costo_ast(orig_ast)
    c_sop = costo_ast(ast_sop_desde_cubos(rs.cobertura, n))
    c_pos = costo_ast(ast_pos_desde_cubos_complemento(rp.cobertura, n))
    v_sop = validar(f, sop)
    v_pos = validar(f, pos)
    # equivalencia original(AST) vs simplificada (solo sin indiferentes)
    eq_orig = None
    if not dc:
        eq_orig = equivalencia_ast(orig_ast, parsear_expresion(sop), n)
    def red(a, b):
        return 0.0 if a == 0 else round(100.0 * (a - b) / a, 1)
    mejor = c_sop if (c_sop["literales"], c_sop["compuertas"]) <= (c_pos["literales"], c_pos["compuertas"]) else c_pos
    return {
        "id": caso.id, "nombre": caso.nombre, "n": n, "entrada": f.descripcion or "", "nota": caso.nota,
        "minterminos": sorted(unos), "indiferentes": sorted(dc),
        "original": a_str(orig_ast) if len(a_str(orig_ast)) < 400 else a_str(orig_ast)[:60] + " …",
        "sop": sop, "pos": pos,
        "num_primos": len(rs.primos), "num_esenciales": len(rs.esenciales), "usa_petrick": rs.usa_petrick,
        "soluciones_minimas": len(rs.soluciones_minimas), "exacto": rs.exacto,
        "costo_original": c_orig, "costo_sop": c_sop, "costo_pos": c_pos,
        "red_literales_sop": red(c_orig["literales"], c_sop["literales"]),
        "red_compuertas_sop": red(c_orig["compuertas"], c_sop["compuertas"]),
        "red_literales_pos": red(c_orig["literales"], c_pos["literales"]),
        "red_compuertas_pos": red(c_orig["compuertas"], c_pos["compuertas"]),
        "valid_sop": v_sop, "valid_pos": v_pos, "equiv_original": eq_orig,
        "tiempo_ms": round(t_ms, 3),
        "primos": [cubo_a_producto(p, n) for p in rs.primos],
        "esenciales": [cubo_a_producto(p, n) for p in rs.esenciales],
        "alternativas": [" + ".join(sorted(cubo_a_producto(c, n) for c in s)) for s in rs.soluciones_minimas],
        "cubos_sop": [list(c) for c in rs.cobertura],
    }


# -------------------------------------------------------------- benchmark
def _instancia(n, rnd):
    p = rnd.choice([0.25, 0.5, 0.75])
    unos = [i for i in range(2 ** n) if rnd.random() < p]
    return unos


def _tiempo_y_primos(n, unos, dc=()):
    t0 = time.perf_counter()
    r = minimizar_sop(n, unos, dc)
    t = (time.perf_counter() - t0) * 1000.0
    return t, len(r.primos), r


def peor_caso_primos(n, rnd, iteraciones):
    """Busqueda local (hill-climbing) del maximo numero de implicantes primos encontrado."""
    mejor = [i for i in range(2 ** n) if rnd.random() < 0.6]
    mejor_p = len(primos_implicantes(n, mejor, [])[0])
    for _ in range(iteraciones):
        cand = set(mejor)
        for _ in range(rnd.choice([1, 2, 3])):
            cand ^= {rnd.randrange(2 ** n)}
        p = len(primos_implicantes(n, sorted(cand), [])[0])
        if p >= mejor_p:
            mejor, mejor_p = sorted(cand), p
    return mejor, mejor_p


def benchmark(semilla=2026, instancias=None, iter_peor=None):
    rnd = random.Random(semilla)
    instancias = instancias or {2: 200, 3: 200, 4: 200, 5: 150, 6: 100}
    iter_peor = iter_peor or {2: 100, 3: 200, 4: 400, 5: 600, 6: 600}
    filas = []
    for n in range(2, 7):
        ts, ps, ex, pet, ess = [], [], [], 0, []
        for _ in range(instancias[n]):
            unos = _instancia(n, rnd)
            t, p, r = _tiempo_y_primos(n, unos)
            ts.append(t)
            ps.append(p)
            ex.append(r.exacto)
            pet += r.usa_petrick
            ess.append(len(r.esenciales))
        peor, pmax = peor_caso_primos(n, rnd, iter_peor[n])
        tw = statistics.mean(_tiempo_y_primos(n, peor)[0] for _ in range(5))
        paridad = [i for i in range(2 ** n) if bin(i).count("1") % 2 == 1]
        tpar, ppar, _ = _tiempo_y_primos(n, paridad)
        filas.append({
            "n": n, "instancias": instancias[n],
            "t_medio_ms": round(statistics.mean(ts), 4), "t_desv_ms": round(statistics.pstdev(ts), 4),
            "t_max_ms": round(max(ts), 4),
            "primos_medio": round(statistics.mean(ps), 2), "primos_max_aleatorio": max(ps),
            "primos_max_busqueda": pmax, "t_peor_busqueda_ms": round(tw, 4),
            "primos_paridad": ppar, "t_paridad_ms": round(tpar, 4),
            "frac_petrick": round(pet / instancias[n], 3), "todos_exactos": all(ex),
            "cota_3n": 3 ** n, "cota_3n_sobre_n": round(3 ** n / n, 1),
            "esenciales_medio": round(statistics.mean(ess), 2),
        })
    return filas
