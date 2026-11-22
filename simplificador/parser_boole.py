"""parser_boole.py
Entrada de funciones booleanas en dos modos:
  (a) listas de minterminos / maxterminos / indiferentes  (∑m, ∏M, ∑d)
  (b) expresiones simbolicas:  A'B'C + A'BC + AB'C'

Gramatica (precedencia de mayor a menor):
    primario := VAR | 0 | 1 | '(' expr ')'
    postfijo := primario ( "'" )*          # complemento postfijo
    prefijo  := ('!' | '~' | '¬') prefijo | postfijo
    producto := prefijo ( ('*'|'·'|'&'|ε) prefijo )*   # AND explicito o por yuxtaposicion
    xor      := producto ( ('^'|'⊕') producto )*
    suma     := xor ( ('+'|'|') xor )*

AST: tuplas ('var',x) ('const',0|1) ('not',a) ('and',[..]) ('or',[..]) ('xor',a,b)
Autoria propia; solo biblioteca estandar.
"""
import re
from dataclasses import dataclass, field

NOMBRES = "ABCDEF"


@dataclass
class FuncionBooleana:
    """Funcion f:{0,1}^n -> {0,1,X} representada por conjuntos de indices."""
    n: int
    minterminos: frozenset
    indiferentes: frozenset = field(default_factory=frozenset)
    ast: object = None            # AST original si la entrada fue simbolica
    forma_original: str = "sop"   # 'sop' | 'pos' | 'expr'
    descripcion: str = ""

    @property
    def vars(self):
        return list(NOMBRES[: self.n])

    @property
    def maxterminos(self):
        todos = set(range(2 ** self.n))
        return frozenset(todos - set(self.minterminos) - set(self.indiferentes))


# ---------------------------------------------------------------- tokenizador
def _tokens(texto):
    texto = texto.replace("’", "'").replace("`", "'").replace("′", "'")
    out, i = [], 0
    while i < len(texto):
        c = texto[i]
        if c.isspace():
            i += 1
        elif c.isalpha():
            if c.upper() not in NOMBRES:
                raise ValueError(f"Variable no soportada: '{c}' (use A..F)")
            out.append(("VAR", c.upper()))
            i += 1
        elif c in "01":
            out.append(("CONST", int(c)))
            i += 1
        elif c in "()'":
            out.append((c, c))
            i += 1
        elif c in "!~¬":
            out.append(("NOT", c))
            i += 1
        elif c in "*·&.∧":
            out.append(("AND", c))
            i += 1
        elif c in "+|∨":
            out.append(("OR", c))
            i += 1
        elif c in "^⊕":
            out.append(("XOR", c))
            i += 1
        else:
            raise ValueError(f"Caracter no reconocido: '{c}'")
    return out


class _Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i][0] if self.i < len(self.t) else None

    def eat(self, k=None):
        tok = self.t[self.i]
        if k and tok[0] != k:
            raise ValueError(f"Se esperaba {k} y se encontro {tok}")
        self.i += 1
        return tok

    def suma(self):
        hs = [self.xor()]
        while self.peek() == "OR":
            self.eat()
            hs.append(self.xor())
        return hs[0] if len(hs) == 1 else ("or", hs)

    def xor(self):
        a = self.producto()
        while self.peek() == "XOR":
            self.eat()
            a = ("xor", a, self.producto())
        return a

    def producto(self):
        hs = [self.prefijo()]
        while True:
            p = self.peek()
            if p == "AND":
                self.eat()
                hs.append(self.prefijo())
            elif p in ("VAR", "CONST", "(", "NOT"):
                hs.append(self.prefijo())
            else:
                break
        return hs[0] if len(hs) == 1 else ("and", hs)

    def prefijo(self):
        if self.peek() == "NOT":
            self.eat()
            return ("not", self.prefijo())
        return self.postfijo()

    def postfijo(self):
        a = self.primario()
        while self.peek() == "'":
            self.eat()
            a = ("not", a)
        return a

    def primario(self):
        p = self.peek()
        if p == "VAR":
            return ("var", self.eat()[1])
        if p == "CONST":
            return ("const", self.eat()[1])
        if p == "(":
            self.eat()
            e = self.suma()
            self.eat(")")
            return e
        raise ValueError(f"Token inesperado: {self.t[self.i] if self.i < len(self.t) else 'fin'}")


def parsear_expresion(texto):
    """Devuelve el AST de una expresion booleana."""
    p = _Parser(_tokens(texto))
    ast = p.suma()
    if p.i != len(p.t):
        raise ValueError("Sobran simbolos al final de la expresion")
    return ast


def variables_de(ast, acc=None):
    acc = set() if acc is None else acc
    k = ast[0]
    if k == "var":
        acc.add(ast[1])
    elif k == "not":
        variables_de(ast[1], acc)
    elif k in ("and", "or"):
        for h in ast[1]:
            variables_de(h, acc)
    elif k == "xor":
        variables_de(ast[1], acc)
        variables_de(ast[2], acc)
    return acc


def evaluar(ast, asig):
    k = ast[0]
    if k == "var":
        return asig[ast[1]]
    if k == "const":
        return ast[1]
    if k == "not":
        return 1 - evaluar(ast[1], asig)
    if k == "and":
        return int(all(evaluar(h, asig) for h in ast[1]))
    if k == "or":
        return int(any(evaluar(h, asig) for h in ast[1]))
    if k == "xor":
        return evaluar(ast[1], asig) ^ evaluar(ast[2], asig)
    raise ValueError(k)


def asignacion(idx, n):
    """Indice -> dict variable->bit (A es el bit mas significativo)."""
    return {NOMBRES[j]: (idx >> (n - 1 - j)) & 1 for j in range(n)}


def a_str(ast):
    """AST -> cadena Unicode (yuxtaposicion para AND, ' para complemento)."""
    def rec(a, padre=None):
        k = a[0]
        if k == "var":
            return a[1]
        if k == "const":
            return str(a[1])
        if k == "not":
            h = a[1]
            if h[0] in ("var", "const"):
                return rec(h) + "'"
            return "(" + rec(h) + ")'"
        if k == "and":
            partes = [rec(h, "and") for h in a[1]]
            todos_lit = all(h[0] == "var" or (h[0] == "not" and h[1][0] == "var") for h in a[1])
            return ("" if todos_lit else "·").join(partes)
        if k == "or":
            s = " + ".join(rec(h, "or") for h in a[1])
            return "(" + s + ")" if padre in ("and", "xor") else s
        if k == "xor":
            s = rec(a[1], "xor") + " ⊕ " + rec(a[2], "xor")
            return "(" + s + ")" if padre in ("and",) else s
        raise ValueError(k)
    return rec(ast)


# ------------------------------------------------------------ constructores
def desde_listas(n, minterminos=(), indiferentes=(), maxterminos=None, descripcion=""):
    """Modo (a): ∑m(...) + ∑d(...)  o  ∏M(...) + ∑d(...)."""
    if not 2 <= n <= 6:
        raise ValueError("n debe estar entre 2 y 6")
    total = set(range(2 ** n))
    d = set(indiferentes)
    if maxterminos is not None:
        M = set(maxterminos)
        m = total - M - d
        forma = "pos"
    else:
        m = set(minterminos)
        forma = "sop"
    if not (m | d) <= total:
        raise ValueError("Indices fuera de rango 0..2^n-1")
    if m & d:
        raise ValueError("Un indice no puede ser minitermino e indiferente a la vez")
    return FuncionBooleana(n, frozenset(m), frozenset(d), None, forma, descripcion)


def desde_expresion(texto, n=None, descripcion=""):
    ast = parsear_expresion(texto)
    vs = variables_de(ast)
    if n is None:
        n = max([NOMBRES.index(v) for v in vs] + [1]) + 1
    if any(NOMBRES.index(v) >= n for v in vs):
        raise ValueError("La expresion usa variables fuera de las n declaradas")
    m = frozenset(i for i in range(2 ** n) if evaluar(ast, asignacion(i, n)))
    return FuncionBooleana(n, m, frozenset(), ast, "expr", descripcion or texto)


_RE_LISTA = re.compile(r"(∑|∏|S|P|sum|prod)?\s*(m|M|d|D)\s*\(([^)]*)\)", re.I)


def desde_texto_listas(n, texto):
    """Interpreta 'm(1,3,5) + d(0,2)' o '∏M(0,1) + d(7)'."""
    m, M, d = [], None, []
    for _, tipo, lst in _RE_LISTA.findall(texto):
        vals = [int(x) for x in lst.replace(" ", "").split(",") if x != ""]
        if tipo == "m":
            m += vals
        elif tipo == "M":
            M = (M or []) + vals
        else:
            d += vals
    if M is not None and m:
        raise ValueError("Mezcla de minterminos y maxterminos")
    return desde_listas(n, m, d, M, descripcion=texto)
