"""algebra_boole.py
Motor de simplificacion algebraica paso a paso con traza de leyes.

Fases (cada transformacion se registra con el nombre de la ley aplicada):
  A. Reescritura del AST hasta una suma de productos (SOP):
     Complemento de constantes, Doble negacion, De Morgan, definicion de XOR,
     Nulidad, Identidad, Asociativa, Distributiva.
  B. Simplificacion de terminos: Idempotencia, Complemento (XX'=0), Nulidad.
  C. Iteracion de Adyacencia (XY + XY' = X, que se deriva de Distributiva +
     Complemento + Identidad), Idempotencia (X = X + X) para reutilizar
     terminos, Absorcion (X + XY = X) y Consenso (XY + X'Z + YZ = XY + X'Z).
La Conmutativa se registra al ordenar literales/terminos.
Autoria propia; solo biblioteca estandar.
"""
from dataclasses import dataclass
from .parser_boole import a_str, NOMBRES

LEYES = ["Identidad", "Nulidad", "Idempotencia", "Complemento", "Doble negación",
         "Conmutativa", "Asociativa", "Distributiva", "Absorción", "Adyacencia",
         "Consenso", "De Morgan", "Definición de ⊕"]


@dataclass
class Paso:
    n: int
    ley: str
    detalle: str
    expresion: str


# --------------------------------------------------------------- fase A (AST)
def _rewrite_once(a):
    """Aplica UNA reescritura (la mas externa/izquierda). Devuelve (nuevo, ley, detalle) o None."""
    k = a[0]
    if k == "not":
        h = a[1]
        if h[0] == "const":
            return ("const", 1 - h[1]), "Complemento", f"{a_str(a)} = {1 - h[1]}"
        if h[0] == "not":
            return h[1], "Doble negación", f"({a_str(h[1])})'' = {a_str(h[1])}"
        if h[0] == "and":
            n = ("or", [("not", x) for x in h[1]])
            return n, "De Morgan", f"{a_str(a)} = {a_str(n)}"
        if h[0] == "or":
            n = ("and", [("not", x) for x in h[1]])
            return n, "De Morgan", f"{a_str(a)} = {a_str(n)}"
        if h[0] == "xor":
            n = ("not", _xor_def(h))
            return n, "Definición de ⊕", f"{a_str(h)} = {a_str(_xor_def(h))}"
    if k == "xor":
        n = _xor_def(a)
        return n, "Definición de ⊕", f"{a_str(a)} = {a_str(n)}"
    if k in ("and", "or"):
        hs = a[1]
        # Asociativa: aplanar
        for i, h in enumerate(hs):
            if h[0] == k:
                nuevo = hs[:i] + h[1] + hs[i + 1:]
                det = "X·(Y·Z) = X·Y·Z" if k == "and" else "X + (Y + Z) = X + Y + Z"
                return (k, nuevo), "Asociativa", det
        cte_id, cte_nul = (1, 0) if k == "and" else (0, 1)
        if any(h == ("const", cte_nul) for h in hs):
            return ("const", cte_nul), "Nulidad", f"{a_str(a)} = {cte_nul}"
        if any(h == ("const", cte_id) for h in hs):
            nuevo = [h for h in hs if h != ("const", cte_id)]
            r = ("const", cte_id) if not nuevo else (nuevo[0] if len(nuevo) == 1 else (k, nuevo))
            return r, "Identidad", f"{a_str(a)} = {a_str(r)}"
        if k == "and":
            for i, h in enumerate(hs):
                if h[0] == "or":
                    resto = hs[:i] + hs[i + 1:]
                    n = ("or", [("and", resto + [alt]) for alt in h[1]])
                    return n, "Distributiva", f"{a_str(a)} = {a_str(n)}"
        # recursion en hijos
        for i, h in enumerate(hs):
            r = _rewrite_once(h)
            if r:
                return (k, hs[:i] + [r[0]] + hs[i + 1:]), r[1], r[2]
    if k == "not":
        r = _rewrite_once(a[1])
        if r:
            return ("not", r[0]), r[1], r[2]
    return None


def _xor_def(a):
    x, y = a[1], a[2]
    return ("or", [("and", [x, ("not", y)]), ("and", [("not", x), y])])


def _a_sop(ast):
    pasos = []
    actual = ast
    for _ in range(500):
        r = _rewrite_once(actual)
        if not r:
            break
        actual, ley, det = r
        pasos.append((ley, det, a_str(actual)))
    return actual, pasos


# ------------------------------------------------------- fase B/C (terminos)
def _lit_str(l):
    return NOMBRES[l[0]] + ("" if l[1] else "'")


def _term_str(t):
    return "1" if not t else "".join(_lit_str(l) for l in t)


def _sop_str(terms):
    return "0" if not terms else " + ".join(_term_str(t) for t in terms)


def _ast_a_terminos(a):
    """AST ya en SOP -> lista de listas de literales (var, pol) o constantes."""
    if a[0] == "const":
        return [[("c", a[1])]] if a[1] else []

    def lit(x):
        if x[0] == "var":
            return (NOMBRES.index(x[1]), 1)
        if x[0] == "not" and x[1][0] == "var":
            return (NOMBRES.index(x[1][1]), 0)
        if x[0] == "const":
            return ("c", x[1])
        raise ValueError("No esta en SOP: " + a_str(x))

    hs = a[1] if a[0] == "or" else [a]
    out = []
    for h in hs:
        if h[0] == "and":
            out.append([lit(x) for x in h[1]])
        else:
            out.append([lit(h)])
    return out


class Simplificador:
    """Registra la traza algebraica. Uso: Simplificador().simplificar(ast) -> (terminos, traza)."""

    def __init__(self):
        self.traza = []

    def _log(self, ley, detalle, terms):
        self.traza.append(Paso(len(self.traza), ley, detalle, _sop_str(terms)))

    # ------------------------------------------------------------------
    def desde_minterminos(self, n, minterminos):
        terms = [tuple((j, (m >> (n - 1 - j)) & 1) for j in range(n)) for m in sorted(minterminos)]
        return terms

    def simplificar(self, ast=None, terminos_iniciales=None, mostrar_inicial=True):
        self.traza = []
        if ast is not None:
            if mostrar_inicial:
                self.traza.append(Paso(0, "Expresión inicial", "", a_str(ast)))
            sop, pasos = _a_sop(ast)
            for ley, det, ex in pasos:
                self.traza.append(Paso(len(self.traza), ley, det, ex))
            raw = _ast_a_terminos(sop)
        else:
            raw = [list(t) for t in terminos_iniciales]
            self.traza.append(Paso(0, "Expresión inicial", "forma canónica (suma de minterminos)", _sop_str([tuple(t) for t in raw])))
        terms = self._limpiar_terminos(raw)
        terms = self._bucle(terms)
        self._log("Resultado", "forma SOP simplificada algebraicamente", terms)
        return terms, self.traza

    # --- limpieza dentro de cada termino -------------------------------
    def _limpiar_terminos(self, raw):
        out = []
        if any([l for l in t if l[0] != "c"] != sorted([l for l in t if l[0] != "c"]) for t in raw):
            self._log("Conmutativa", "se ordenan los literales de cada término (XY = YX)",
                      [tuple(sorted(l for l in t if l[0] != "c")) for t in raw])
        for idx, t in enumerate(raw):
            rest = [tuple(sorted(l for l in x if l[0] != 'c')) for x in raw[idx + 1:]]
            # constantes
            if any(l[0] == "c" and l[1] == 0 for l in t):
                self._log("Nulidad", "el término con factor 0 vale 0 (X·0 = 0): se elimina", out + rest)
                continue
            t2 = [l for l in t if l[0] != "c"]
            if len(t2) != len(t):
                pass
            # contradiccion e idempotencia
            vistos = {}
            contra = False
            dup = False
            ordenado = []
            for l in t2:
                if l[0] in vistos:
                    if vistos[l[0]] != l[1]:
                        contra = True
                    else:
                        dup = True
                else:
                    vistos[l[0]] = l[1]
                    ordenado.append(l)
            if contra:
                v = [j for j in vistos]
                self._log("Complemento", f"{_term_str(tuple(t2))} contiene X·X' = 0; por Nulidad el término vale 0 y se elimina", out + rest)
                continue
            if dup:
                self._log("Idempotencia", f"{_term_str(tuple(t2))}: X·X = X", out + [tuple(sorted(ordenado))] + rest)
            ordenado = tuple(sorted(ordenado))
            out.append(ordenado)
        return out

    # --- bucle principal -------------------------------------------------
    def _bucle(self, terms):
        if any(len(t) == 0 for t in terms):
            self._log("Nulidad", "un término vale 1; X + 1 = 1", [()])
            return [()]
        terms = self._dedup(terms)
        for _ in range(200):
            cambio = False
            terms, c = self._adyacencia(terms)
            cambio |= c
            terms, c = self._dedup_(terms)
            cambio |= c
            terms, c = self._absorcion(terms)
            cambio |= c
            if any(len(t) == 0 for t in terms):
                self._log("Nulidad", "un término vale 1; X + 1 = 1", [()])
                return [()]
            if not cambio:
                terms, c = self._consenso(terms)
                if not c:
                    break
        return terms

    def _dedup(self, terms):
        return self._dedup_(terms)[0]

    def _dedup_(self, terms):
        vistos, out = set(), []
        for t in terms:
            if t in vistos:
                continue
            vistos.add(t)
            out.append(t)
        if len(out) != len(terms):
            rep = [t for t in terms if terms.count(t) > 1]
            self._log("Idempotencia", f"X + X = X ({_term_str(rep[0])} repetido)", out)
            return out, True
        return out, False

    def _adyacencia(self, terms):
        """Un paso de adyacencia: combina pares XY + XY' = X (reutilizando terminos via X = X + X)."""
        cambio = False
        pares = []
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                a, b = terms[i], terms[j]
                if len(a) != len(b):
                    continue
                da = {l[0]: l[1] for l in a}
                db = {l[0]: l[1] for l in b}
                if set(da) != set(db):
                    continue
                dif = [v for v in da if da[v] != db[v]]
                if len(dif) == 1:
                    comun = tuple(l for l in a if l[0] != dif[0])
                    pares.append((i, j, comun, dif[0]))
        if not pares:
            return terms, False
        uso = {}
        for i, j, _, _ in pares:
            uso[i] = uso.get(i, 0) + 1
            uso[j] = uso.get(j, 0) + 1
        # duplicar terminos que se reutilizan (X = X + X)
        actual = list(terms)
        copias = {i: [i] for i in range(len(terms))}
        reus = [i for i, c in uso.items() if c > 1]
        if reus:
            # representacion con contadores
            items = [(t, k) for k, t in enumerate(terms)]
            extra = []
            for i in reus:
                extra += [terms[i]] * (uso[i] - 1)
            nombres = ", ".join(_term_str(terms[i]) + (f" (×{uso[i]})" if uso[i] > 1 else "") for i in reus)
            actual = list(terms) + extra
            self._log("Idempotencia", f"X = X + X: se duplican {nombres} para usarlos en más de una adyacencia", actual)
        # aplicar cada adyacencia, consumiendo copias
        pool = {}
        for t in actual:
            pool[t] = pool.get(t, 0) + 1
        nuevos = []
        orden = list(actual)
        for i, j, comun, v in pares:
            a, b = terms[i], terms[j]
            if pool.get(a, 0) < 1 or pool.get(b, 0) < 1:
                continue
            pool[a] -= 1
            pool[b] -= 1
            orden.remove(a)
            orden.remove(b)
            orden.append(comun)
            self._log("Adyacencia",
                      f"{_term_str(a)} + {_term_str(b)} = {_term_str(comun)}({NOMBRES[v]} + {NOMBRES[v]}') = {_term_str(comun)}",
                      orden)
            cambio = True
        # terminos que quedan en el pool vuelven al conjunto
        return orden, cambio

    def _absorcion(self, terms):
        cambio = False
        out = list(terms)
        for a in list(out):
            for b in list(out):
                if a is b or a == b:
                    continue
                if set(a) < set(b) and b in out:
                    out.remove(b)
                    self._log("Absorción", f"{_term_str(a)} + {_term_str(b)} = {_term_str(a)}  (X + XY = X)", out)
                    cambio = True
        return out, cambio

    def _consenso(self, terms):
        for i, a in enumerate(terms):
            for j, b in enumerate(terms):
                if j <= i:
                    continue
                da = dict(a)
                db = dict(b)
                opuestas = [v for v in da if v in db and da[v] != db[v]]
                if len(opuestas) != 1:
                    continue
                x = opuestas[0]
                cons = {v: p for v, p in list(da.items()) + list(db.items()) if v != x}
                if any(v in da and v in db and da[v] != db[v] for v in cons):
                    continue
                ct = tuple(sorted(cons.items()))
                for c in terms:
                    if c is a or c is b:
                        continue
                    if c == ct:
                        out = [t for t in terms if t is not c]
                        self._log("Consenso",
                                  f"{_term_str(a)} + {_term_str(b)} + {_term_str(c)} = {_term_str(a)} + {_term_str(b)}  (XY + X'Z + YZ = XY + X'Z)",
                                  out)
                        return out, True
        return terms, False


def simplificar_algebraicamente(ast=None, n=None, minterminos=None):
    s = Simplificador()
    if ast is not None:
        terms, traza = s.simplificar(ast=ast)
    else:
        terms, traza = s.simplificar(terminos_iniciales=s.desde_minterminos(n, minterminos))
    return terms, traza


def terms_a_implicantes(terms, n):
    """Lista de terminos (var,pol) -> lista de (valor, mascara) donde mascara=1 indica variable ausente."""
    res = []
    for t in terms:
        val = mask = 0
        presentes = {l[0]: l[1] for l in t}
        for j in range(n):
            bit = 1 << (n - 1 - j)
            if j in presentes:
                if presentes[j]:
                    val |= bit
            else:
                mask |= bit
        res.append((val, mask))
    return res
