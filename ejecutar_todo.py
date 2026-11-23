"""ejecutar_todo.py  -  Reproduce TODOS los resultados del informe (casos, benchmark, figuras).
Uso:  python ejecutar_todo.py            (genera resultados/ y figuras/)
"""
import json, os, sys, time, platform
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from simplificador.validador_benchmark import casos_obligatorios, ejecutar_caso, benchmark
from simplificador.quine_mccluskey import minimizar_sop, cubo_a_producto
from simplificador.kmap_visualizer import figura_kmap, dibujar_kmap, leyenda_grupos, COLORES
from simplificador.algebra_boole import simplificar_algebraicamente
from simplificador.parser_boole import desde_expresion

RAIZ = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(RAIZ, "figuras")
RES = os.path.join(RAIZ, "resultados")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)
DPI = 300
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
AZUL, ROJO, VERDE, GRIS = "#1f5f99", "#c0462c", "#2a8a57", "#6b6b6b"


def fig1():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")
    def caja(x, y, w, h, txt, fc="#eef3f8", ec=AZUL, fs=9.5, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1.4))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")
    def flecha(x1, y1, x2, y2, txt=""):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, color="#333333", lw=1.3))
        if txt:
            ax.text((x1 + x2) / 2 + 0.8, (y1 + y2) / 2 + 1.2, txt, fontsize=7.5, color=GRIS, ha="left")
    caja(3, 50, 26, 9, "Entrada del usuario\n∑m, ∏M, ∑d  /  expresión\nsimbólica (CLI o tests)", "#fff6e5", "#b07d00", bold=True)
    caja(37, 50, 26, 9, "parser_boole.py\nAST · FuncionBooleana\n(n, minterminos, X)", bold=True)
    caja(71, 50, 26, 9, "Tabla de verdad\n2ⁿ filas (n = 2..6)", "#f2f2f2", GRIS)
    flecha(29, 54.5, 37, 54.5); flecha(63, 54.5, 71, 54.5)
    caja(3, 30, 28, 10, "algebra_boole.py\nTraza paso a paso\nde leyes de Boole", bold=True)
    caja(36, 30, 28, 10, "quine_mccluskey.py\nPrimos · esenciales ·\nPetrick → SOP / POS", bold=True)
    caja(69, 30, 28, 10, "kmap_visualizer.py\nK-Map 2–4 var (Gray)\nagrupos + PNG 300 dpi", bold=True)
    flecha(50, 50, 17, 40, "AST"); flecha(50, 50, 50, 40, "m, d"); flecha(78, 50, 83, 40, "m, d, grupos")
    flecha(64, 35, 69, 35, "cubos")
    caja(3, 9, 40, 12, "validador_benchmark.py\nEquivalencia exhaustiva (2ⁿ) · literales y\ncompuertas · tiempos · benchmark", "#eaf5ee", VERDE, bold=True)
    caja(52, 9, 45, 12, "Salidas\nExpresión mínima SOP/POS · traza\nTablas CSV/JSON · figuras PNG · log de pruebas", "#fff6e5", "#b07d00", bold=True, fs=8.8)
    flecha(17, 30, 17, 21); flecha(50, 30, 30, 21); flecha(83, 30, 76, 21)
    flecha(43, 15, 52, 15)
    ax.text(47.5, 16.6, "resultados", fontsize=7.5, color=GRIS, ha="center")
    ax.text(50, 3.2, "cli.py: interfaz de línea de comandos que orquesta todos los módulos", ha="center", fontsize=9, style="italic", color=GRIS)
    ax.set_title("Arquitectura modular y flujo de datos del simplificador lógico", fontsize=12, pad=6)
    fig.savefig(os.path.join(FIG, "fig1_arquitectura_sistema.png"), dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig_kmaps(res):
    byid = {r["id"]: r for r in res}
    # fig2: 3 variables
    r = byid["1"]
    q = minimizar_sop(3, r["minterminos"], [])
    figura_kmap(os.path.join(FIG, "fig2_kmap_3var_normal.png"), 3, r["minterminos"], [], q.cobertura, q.expresion_sop(),
                "Caso 1 – K-Map de 3 variables  f = ∑m(1,3,5,6,7)", DPI)
    # fig3: toroidal
    r = byid["2"]
    q = minimizar_sop(4, r["minterminos"], [])
    figura_kmap(os.path.join(FIG, "fig3_kmap_4var_toroidal.png"), 4, r["minterminos"], [], q.cobertura, q.expresion_sop(),
                "Caso 2 – K-Map de 4 variables con esquinas envolventes", DPI)
    # fig4: don't care
    r = byid["3"]
    unos, dc = r["minterminos"], r["indiferentes"]
    qa = minimizar_sop(4, unos, [])
    qb = minimizar_sop(4, unos, dc)
    fig = plt.figure(figsize=(12.4, 6.6))
    for k, (q, d, tit) in enumerate([(qa, [], "(a) Sin indiferentes (X tratadas como 0)"), (qb, dc, "(b) Con indiferentes (X usadas)")]):
        ax = fig.add_axes([0.03 + 0.5 * k, 0.30, 0.44, 0.6])
        dibujar_kmap(ax, 4, unos, d, q.cobertura, tit)
        y = 0.22
        for i, t in enumerate(leyenda_grupos(4, q.cobertura)):
            fig.text(0.07 + 0.5 * k, y, "■", color=COLORES[i % 6], fontsize=14, va="center")
            fig.text(0.105 + 0.5 * k, y, t, fontsize=10, va="center")
            y -= 0.045
        fig.text(0.25 + 0.5 * k, 0.03, f"f = {q.expresion_sop()}   ({sum(len(cubo_a_producto(c,4).replace(chr(39),'')) for c in q.cobertura)} literales)",
                 ha="center", fontsize=11.5, fontweight="bold")
    fig.savefig(os.path.join(FIG, "fig4_kmap_4var_dontcare.png"), dpi=DPI, facecolor="white")
    plt.close(fig)


def fig5(res):
    ids = [r["id"] for r in res]
    lo = [r["costo_original"]["literales"] for r in res]
    ls = [r["costo_sop"]["literales"] for r in res]
    go = [r["costo_original"]["compuertas"] for r in res]
    gs = [r["costo_sop"]["compuertas"] for r in res]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    x = range(len(ids)); w = 0.38
    for ax, o, s, tit, yl in [(axs[0], lo, ls, "Literales", "Número de literales"), (axs[1], go, gs, "Compuertas lógicas", "Número de compuertas (AND+OR+NOT)")]:
        b1 = ax.bar([i - w / 2 for i in x], o, w, label="Original", color="#9aa8b8")
        b2 = ax.bar([i + w / 2 for i in x], s, w, label="Simplificada (SOP)", color=AZUL)
        ax.set_xticks(list(x)); ax.set_xticklabels(ids); ax.set_xlabel("Caso de prueba"); ax.set_ylabel(yl)
        ax.set_title(tit, fontsize=11); ax.grid(axis="y", alpha=0.25); ax.set_axisbelow(True)
        for b, v in list(zip(b1, o)) + list(zip(b2, s)):
            ax.text(b.get_x() + b.get_width() / 2, v + max(o) * 0.012, str(v), ha="center", fontsize=7)
        ax.legend(frameon=False, fontsize=8.5)
    fig.suptitle("Reducción de literales y compuertas: original vs. simplificada", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_reduccion_compuertas.png"), dpi=DPI, facecolor="white")
    plt.close(fig)


def fig6(bm):
    ns = [r["n"] for r in bm]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    ax = axs[0]
    ax.plot(ns, [r["t_medio_ms"] for r in bm], "o-", color=AZUL, label="Aleatorias: media")
    ax.plot(ns, [r["t_max_ms"] for r in bm], "s--", color=ROJO, label="Aleatorias: máximo")
    ax.plot(ns, [r["t_peor_busqueda_ms"] for r in bm], "^:", color=VERDE, label="Peor caso (búsqueda local)")
    ax.set_yscale("log"); ax.set_xticks(ns); ax.set_xlabel("Número de variables n"); ax.set_ylabel("Tiempo de ejecución QM+Petrick (ms)")
    ax.set_title("Tiempo de ejecución", fontsize=11); ax.grid(alpha=0.25, which="both"); ax.legend(frameon=False, fontsize=8)
    ax = axs[1]
    ax.plot(ns, [r["primos_medio"] for r in bm], "o-", color=AZUL, label="Media (aleatorias)")
    ax.plot(ns, [r["primos_max_aleatorio"] for r in bm], "s--", color=ROJO, label="Máximo (aleatorias)")
    ax.plot(ns, [r["primos_max_busqueda"] for r in bm], "^:", color=VERDE, label="Máximo hallado (búsqueda local)")
    ax.plot(ns, [r["cota_3n_sobre_n"] for r in bm], "-", color=GRIS, lw=1.2, label="Referencia 3ⁿ/n")
    ax.set_yscale("log"); ax.set_xticks(ns); ax.set_xlabel("Número de variables n"); ax.set_ylabel("Implicantes primos")
    ax.set_title("Crecimiento de implicantes primos", fontsize=11); ax.grid(alpha=0.25, which="both"); ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Escalabilidad empírica del motor exacto (n = 2..6)", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_escalabilidad_complejidad.png"), dpi=DPI, facecolor="white")
    plt.close(fig)


def solo_figuras():
    res = json.load(open(os.path.join(RES, "resultados_casos.json"), encoding="utf-8"))
    bm = json.load(open(os.path.join(RES, "benchmark.json"), encoding="utf-8"))
    fig1(); fig_kmaps(res); fig5(res); fig6(bm)


def main():
    t0 = time.time()
    casos = casos_obligatorios()
    res = [ejecutar_caso(c) for c in casos]
    json.dump(res, open(os.path.join(RES, "resultados_casos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # traza algebraica del caso 1
    f = casos[0].f
    terms, traza = simplificar_algebraicamente(ast=f.ast)
    tr = [{"n": p.n, "ley": p.ley, "detalle": p.detalle, "expresion": p.expresion} for p in traza]
    json.dump(tr, open(os.path.join(RES, "traza_caso1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("== CASOS ==")
    for r in res:
        print(f"Caso {r['id']:>2} n={r['n']} SOP={r['sop'][:60]} | lit {r['costo_original']['literales']}->{r['costo_sop']['literales']} "
              f"| comp {r['costo_original']['compuertas']}->{r['costo_sop']['compuertas']} | valid={r['valid_sop']['equivalente']}/{r['valid_pos']['equivalente']} | {r['tiempo_ms']} ms")
    bm = benchmark()
    json.dump(bm, open(os.path.join(RES, "benchmark.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import csv
    with open(os.path.join(RES, "benchmark.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bm[0].keys())); w.writeheader(); w.writerows(bm)
    print("== BENCHMARK ==")
    for r in bm:
        print(r)
    fig1(); fig_kmaps(res); fig5(res); fig6(bm)
    entorno = {"python": sys.version.split()[0], "plataforma": platform.platform()}
    json.dump(entorno, open(os.path.join(RES, "entorno.json"), "w"), indent=1)
    print(f"Listo en {time.time()-t0:.1f} s. Figuras en {FIG}")


if __name__ == "__main__":
    if "--solo-figuras" in sys.argv:
        solo_figuras()
    else:
        main()
