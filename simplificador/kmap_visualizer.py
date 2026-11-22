"""kmap_visualizer.py
Mapas de Karnaugh de 2, 3 y 4 variables con orden Gray (00,01,11,10),
adyacencia toroidal (bordes y esquinas), celdas 0/1/X y exportacion PNG a 300 dpi.
Autoria propia; matplotlib solo para dibujar.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from .parser_boole import NOMBRES
from .quine_mccluskey import cubo_celdas, cubo_a_producto

GRAY2 = [0, 1]
GRAY4 = [0, 1, 3, 2]          # 00,01,11,10
COLORES = ["#1f5f99", "#c0462c", "#2a8a57", "#7b4fa0", "#b07d00", "#4d4d4d"]
ESTILOS = ["-", "--", "-.", ":", "-", "--"]


def disposicion(n):
    """Devuelve (bits_fila, bits_col, orden_filas, orden_cols)."""
    if n == 2:
        return 1, 1, GRAY2, GRAY2
    if n == 3:
        return 1, 2, GRAY2, GRAY4
    if n == 4:
        return 2, 2, GRAY4, GRAY4
    raise ValueError("El K-Map visual soporta 2, 3 y 4 variables")


def celda_de(n, m):
    """minitermino -> (fila, columna) segun el orden Gray."""
    br, bc, of, oc = disposicion(n)
    f = m >> bc
    c = m & ((1 << bc) - 1)
    return of.index(f), oc.index(c)


def _intervalo_ciclico(pos, tam):
    """Posiciones (subconjunto de 0..tam-1) -> (inicio, longitud) cíclico."""
    pos = sorted(set(pos))
    L = len(pos)
    if L == tam:
        return 0, L
    for s in pos:
        if all(((s + k) % tam) in pos for k in range(L)):
            return s, L
    raise ValueError("Grupo no contiguo en el toro")


def piezas_grupo(n, cubo):
    """Rectangulos (r0,c0,alto,ancho, envuelve_f, envuelve_c) que componen un grupo (separa envolventes)."""
    br, bc, of, oc = disposicion(n)
    nf, nc = len(of), len(oc)
    celdas = [celda_de(n, m) for m in cubo_celdas(cubo, n)]
    fs = {f for f, _ in celdas}
    cs = {c for _, c in celdas}
    f0, hf = _intervalo_ciclico(fs, nf)
    c0, wc = _intervalo_ciclico(cs, nc)
    segf = [(f0, hf)] if f0 + hf <= nf else [(f0, nf - f0), (0, f0 + hf - nf)]
    segc = [(c0, wc)] if c0 + wc <= nc else [(c0, nc - c0), (0, c0 + wc - nc)]
    envuelve = len(segf) > 1 or len(segc) > 1
    piezas = []
    for (rf, h) in segf:
        for (cc, w) in segc:
            piezas.append((rf, cc, h, w))
    return piezas, envuelve


def etiquetas_ejes(n):
    br, bc, of, oc = disposicion(n)
    v = NOMBRES[:n]
    fila_vars = v[:br]
    col_vars = v[br:]
    return fila_vars, col_vars, [format(x, f"0{br}b") for x in of], [format(x, f"0{bc}b") for x in oc]


def dibujar_kmap(ax, n, unos, dc=(), grupos=(), titulo="", etiquetas_grupo=None, tam_celda=1.0, mostrar_indices=True):
    """Dibuja el K-Map sobre `ax`. grupos: lista de cubos (valor,mascara)."""
    br, bc, of, oc = disposicion(n)
    nf, nc = len(of), len(oc)
    fv, cv, fl, cl = etiquetas_ejes(n)
    unos, dc = set(unos), set(dc)
    ax.set_xlim(-1.25, nc + 0.15)
    ax.set_ylim(nf + 0.15, -1.25)
    ax.set_aspect("equal")
    ax.axis("off")
    for r in range(nf):
        for c in range(nc):
            ax.add_patch(Rectangle((c, r), 1, 1, fill=False, ec="#222222", lw=1.0))
            m = (of[r] << bc) | oc[c]
            val = "1" if m in unos else ("X" if m in dc else "0")
            col = "#111111" if val == "1" else ("#b36b00" if val == "X" else "#8a8a8a")
            ax.text(c + 0.5, r + 0.52, val, ha="center", va="center", fontsize=15,
                    fontweight="bold" if val != "0" else "normal", color=col, family="DejaVu Sans")
            if mostrar_indices:
                ax.text(c + 0.5, r + 0.84, str(m), ha="center", va="center", fontsize=7, color="#777777")
    # etiquetas de ejes Gray
    for c in range(nc):
        ax.text(c + 0.5, -0.28, cl[c], ha="center", va="center", fontsize=11)
    for r in range(nf):
        ax.text(-0.28, r + 0.5, fl[r], ha="center", va="center", fontsize=11)
    ax.text(nc / 2, -0.78, "".join(cv), ha="center", va="center", fontsize=12, fontweight="bold")
    ax.text(-0.85, nf / 2, "".join(fv), ha="center", va="center", fontsize=12, fontweight="bold", rotation=90)
    # esquina diagonal
    ax.plot([0, -0.55], [0, -0.55], color="#222222", lw=0.8)
    # grupos
    for gi, g in enumerate(grupos):
        color = COLORES[gi % len(COLORES)]
        piezas, env = piezas_grupo(n, g)
        ins = 0.07 + 0.055 * gi
        for (r0, c0, h, w) in piezas:
            ax.add_patch(FancyBboxPatch((c0 + ins, r0 + ins), w - 2 * ins, h - 2 * ins,
                                        boxstyle="round,pad=0,rounding_size=0.18",
                                        fc=color, ec=color, alpha=0.16, lw=0))
            ax.add_patch(FancyBboxPatch((c0 + ins, r0 + ins), w - 2 * ins, h - 2 * ins,
                                        boxstyle="round,pad=0,rounding_size=0.18",
                                        fc="none", ec=color, lw=2.0, ls=ESTILOS[gi % len(ESTILOS)]))
    if titulo:
        ax.set_title(titulo, fontsize=11, pad=4)


def leyenda_grupos(n, grupos, etiquetas=None):
    """Cadenas de leyenda 'G1: A'B (4 celdas, envolvente)'."""
    out = []
    for i, g in enumerate(grupos):
        _, env = piezas_grupo(n, g)
        celdas = len(cubo_celdas(g, n))
        txt = f"G{i+1}: {cubo_a_producto(g, n)}  ({celdas} celdas" + (", envolvente" if env else "") + ")"
        out.append(txt)
    return out


def figura_kmap(ruta, n, unos, dc, grupos, expresion, titulo, dpi=300):
    fig = plt.figure(figsize=(7.2, 6.2))
    ax = fig.add_axes([0.05, 0.28, 0.9, 0.62])
    dibujar_kmap(ax, n, unos, dc, grupos, titulo)
    leyenda = leyenda_grupos(n, grupos)
    y = 0.215
    for i, t in enumerate(leyenda):
        fig.text(0.1, y, "■", color=COLORES[i % len(COLORES)], fontsize=14, va="center")
        fig.text(0.15, y, t, fontsize=10.5, va="center")
        y -= 0.045
    fig.text(0.5, 0.025, f"Expresión mínima:  f = {expresion}", ha="center", fontsize=12, fontweight="bold")
    fig.savefig(ruta, dpi=dpi, facecolor="white")
    plt.close(fig)


def kmap_ascii(n, unos, dc=()):
    """Version de texto del K-Map (util en la CLI)."""
    br, bc, of, oc = disposicion(n)
    fv, cv, fl, cl = etiquetas_ejes(n)
    cab = f"{''.join(fv)}\\{''.join(cv)} | " + "  ".join(cl)
    filas = [cab, "-" * len(cab)]
    for r in range(len(of)):
        celdas = []
        for c in range(len(oc)):
            m = (of[r] << bc) | oc[c]
            celdas.append("1" if m in unos else ("X" if m in dc else "0"))
        filas.append(f"{fl[r]:>{len(''.join(fv)) + 1 + len(''.join(cv))}} | " + "   ".join(celdas))
    return "\n".join(filas)
