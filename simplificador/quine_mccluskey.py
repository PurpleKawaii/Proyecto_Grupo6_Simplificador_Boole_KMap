"""quine_mccluskey.py
Minimizacion exacta SOP/POS (Quine-McCluskey + metodo de Petrick), n = 2..6.

Representacion interna de un implicante (cubo): par (valor, mascara) donde
los bits de `mascara` = 1 son variables ausentes (guion '-'). Un cubo cubre al
minitermino m si (m & ~mascara) == valor.
Autoria propia; solo biblioteca estandar.
"""
from dataclasses import dataclass, field
from itertools import combinations
from .parser_boole import NOMBRES

LIMITE_PETRICK = 2_000     # maximo de productos intermedios antes de pasar a ramificacion y acotamiento
LIMITE_NODOS = 3_000_000   # maximo de nodos de B&B (respaldo)


def cubo_cubre(cubo, m):
    v, k = cubo
    return (m & ~k) == v


def cubo_celdas(cubo, n):
    v, k = cubo
    return [m for m in range(2 ** n) if (m & ~k) == v]


def cubo_a_producto(cubo, n):
    """(valor, mascara) -> cadena SOP, p.ej. (0b0101, 0b1010) -> A'C."""
    v, k = cubo
    s = ""
    for j in range(n):
        b = 1 << (n - 1 - j)
        if k & b:
            continue
        s += NOMBRES[j] + ("" if v & b else "'")
    return s if s else "1"


def cubo_a_suma(cubo, n):
    """Cubo de f' -> clausula de la POS de f (De Morgan): literal opuesto."""
    v, k = cubo
    lits = []
    for j in range(n):
        b = 1 << (n - 1 - j)
        if k & b:
            continue
        lits.append(NOMBRES[j] + ("'" if v & b else ""))
    if not lits:
        return "0"
    return lits[0] if len(lits) == 1 else "(" + " + ".join(lits) + ")"


def literales(cubo, n):
    return n - bin(cubo[1]).count("1")


@dataclass
class ResultadoQM:
    n: int
    primos: list
    esenciales: list
    cobertura: list              # solucion minima elegida (lista de cubos)
    soluciones_minimas: list     # todas las soluciones empatadas
    usa_petrick: bool
    exacto: bool
    tabla_iteraciones: list = field(default_factory=list)
    pi_cubre: dict = field(default_factory=dict)
    restantes_tras_esenciales: list = field(default_factory=list)
    petrick_producto: list = field(default_factory=list)   # forma SOP de la expresion de Petrick
    metodo: str = 'esenciales'

    def expresion_sop(self):
        if not self.cobertura:
            return "0"
        ps = sorted(cubo_a_producto(c, self.n) for c in self.cobertura)
        if ps == ["1"]:
            return "1"
        return " + ".join(ps)


def primos_implicantes(n, unos, dc):
    """Fase de tabulacion de Quine-McCluskey. Devuelve (primos, iteraciones)."""
    actual = {(m, 0) for m in set(unos) | set(dc)}
    primos, iteraciones = set(), []
    while actual:
        grupos = {}
        for c in actual:
            grupos.setdefault(bin(c[0]).count("1"), []).append(c)
        usados, nuevos = set(), set()
        for g in sorted(grupos):
            for a in grupos.get(g, []):
                for b in grupos.get(g + 1, []):
                    if a[1] == b[1]:
                        d = a[0] ^ b[0]
                        if d and (d & (d - 1)) == 0:   # difieren en un solo bit
                            nuevos.add((a[0] & ~d, a[1] | d))
                            usados.update((a, b))
        iteraciones.append({"cubos": len(actual), "combinados": len(nuevos)})
        primos |= actual - usados
        actual = nuevos
    return sorted(primos), iteraciones


def _absorber(productos):
    """Absorcion sobre enteros-mascara (X + XY = X)."""
    productos = sorted(set(productos), key=lambda x: bin(x).count("1"))
    out = []
    for p in productos:
        if not any((q & p) == q for q in out):
            out.append(p)
    return out


def petrick(clausulas):
    """clausulas: lista de mascaras (bit i = candidato i). Devuelve lista de mascaras (SOP tras
    absorcion) o None si excede LIMITE_PETRICK."""
    cl = _absorber(clausulas)              # dominancia de filas: C1 ⊆ C2 => C2 redundante
    prod = [0]
    for c in sorted(cl, key=lambda x: bin(x).count("1")):
        bits = [1 << i for i in range(c.bit_length()) if (c >> i) & 1]
        nuevo = set()
        for p in prod:
            if p & c:
                nuevo.add(p)
            else:
                for b in bits:
                    nuevo.add(p | b)
        prod = _absorber(nuevo)
        if len(prod) > LIMITE_PETRICK:
            return None
    return prod


def _reducir_columnas(cands, cubre, n):
    """Dominancia de columnas con costo: elimina p si otro q lo cubre con no mas literales."""
    cambio = True
    while cambio:
        cambio = False
        for p in list(cands):
            for q in cands:
                if p == q:
                    continue
                if cubre[p] <= cubre[q] and (literales(p, n) > literales(q, n) or
                                              (cubre[p] < cubre[q] and literales(p, n) >= literales(q, n))):
                    cands.remove(p)
                    cambio = True
                    break
    return cands


def _bb_cobertura(cands, cubre, resto, n):
    """Cobertura minima exacta (terminos, literales) por ramificacion y acotamiento."""
    mejor = [None, (10 ** 9, 10 ** 9)]
    nodos = [0]
    abortado = [False]

    def rec(falt, sel, costo):
        nodos[0] += 1
        if nodos[0] > LIMITE_NODOS:
            abortado[0] = True
            return
        if costo >= mejor[1] and mejor[0] is not None:
            return
        if not falt:
            if costo < mejor[1]:
                mejor[0], mejor[1] = list(sel), costo
            return
        m = min(falt, key=lambda x: sum(1 for p in cands if x in cubre[p]))
        for p in sorted((p for p in cands if m in cubre[p]), key=lambda p: -len(cubre[p] & falt)):
            sel.append(p)
            rec(falt - cubre[p], sel, (costo[0] + 1, costo[1] + literales(p, n)))
            sel.pop()
    rec(frozenset(resto), [], (0, 0))
    return mejor[0], abortado[0]


def minimizar_sop(n, unos, dc=()):
    unos, dc = set(unos), set(dc)
    if not unos:
        return ResultadoQM(n, [], [], [], [[]], False, True)
    if len(unos | dc) == 2 ** n and True:
        # funcion constante 1 (con indiferentes se cubre todo)
        pass
    primos, iters = primos_implicantes(n, unos, dc)
    pi_cubre = {p: [m for m in unos if cubo_cubre(p, m)] for p in primos}
    # esenciales
    esenciales = []
    for m in sorted(unos):
        cub = [p for p in primos if cubo_cubre(p, m)]
        if len(cub) == 1 and cub[0] not in esenciales:
            esenciales.append(cub[0])
    cubiertos = {m for p in esenciales for m in unos if cubo_cubre(p, m)}
    resto = sorted(unos - cubiertos)
    usa_petrick = bool(resto)
    soluciones, exacto, prod_petrick = [list(esenciales)], True, []
    metodo = "esenciales"
    if resto:
        candidatos = [p for p in primos if p not in esenciales and any(cubo_cubre(p, m) for m in resto)]
        cubre = {p: frozenset(m for m in resto if cubo_cubre(p, m)) for p in candidatos}
        n_antes = len(candidatos)
        candidatos = _reducir_columnas(list(candidatos), cubre, n)
        # tras la reduccion pueden aparecer nuevos esenciales (se tratan dentro de Petrick)
        idx = {p: i for i, p in enumerate(candidatos)}
        clausulas = []
        for m in resto:
            mask = 0
            for p in candidatos:
                if m in cubre[p]:
                    mask |= 1 << idx[p]
            clausulas.append(mask)
        prod = petrick(clausulas)
        if prod is not None:
            metodo = "Petrick" + (" + dominancia de columnas" if len(candidatos) < n_antes else "")
            sel_list = [[candidatos[i] for i in range(len(candidatos)) if (pm >> i) & 1] for pm in prod]
            prod_petrick = [sorted(x) for x in sel_list]
            def costo(lst):
                return (len(lst), sum(literales(c, n) for c in lst))
            mejor = min(costo(x) for x in sel_list)
            soluciones = [list(esenciales) + x for x in sel_list if costo(x) == mejor]
        else:
            metodo = "ramificación y acotamiento (Petrick excedió el límite)"
            sol, abort = _bb_cobertura(candidatos, cubre, resto, n)
            if abort or sol is None:
                exacto = False
                sel, falt = [], set(resto)
                while falt:
                    mejor_p = max(candidatos, key=lambda p: (len(cubre[p] & falt), -literales(p, n)))
                    sel.append(mejor_p)
                    falt -= cubre[mejor_p]
                sol = sel
                metodo = "voraz (respaldo, no exacto)"
            soluciones = [list(esenciales) + sol]
    soluciones = sorted(sorted(x) for x in soluciones)   # desempate determinista
    sol0 = soluciones[0]
    return ResultadoQM(n, primos, esenciales, sol0, [sorted(s) for s in soluciones], usa_petrick, exacto,
                       iters, pi_cubre, resto, prod_petrick, metodo)


def minimizar_pos(n, unos, dc=()):
    """POS minima = De Morgan sobre la SOP minima de f' (ceros como unos, mismos indiferentes)."""
    ceros = set(range(2 ** n)) - set(unos) - set(dc)
    r = minimizar_sop(n, ceros, dc)
    return r


def expresion_pos(r):
    if not r.cobertura:
        # f' = 0  => f = 1
        return "1"
    cl = sorted(cubo_a_suma(c, r.n) for c in r.cobertura)
    if cl == ["0"]:
        return "0"
    return "·".join(cl)


def contar_primos_n(n, unos, dc=()):
    return len(primos_implicantes(n, unos, dc)[0])
