"""experimento_exhaustivo.py - Verificacion exhaustiva (todas las funciones de n=3 y n=4) y comparacion
entre la traza algebraica y el minimo exacto Quine-McCluskey. Guarda resultados/exhaustivo.json"""
import json, os, random, time
from simplificador.quine_mccluskey import minimizar_sop, minimizar_pos, expresion_pos, cubo_cubre, literales
from simplificador.algebra_boole import simplificar_algebraicamente, terms_a_implicantes
from simplificador.parser_boole import desde_listas
from simplificador.validador_benchmark import validar

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")


def evaluar_todas(n):
    t0 = time.perf_counter()
    malas = 0
    for mask in range(2 ** (2 ** n)):
        ms = [i for i in range(2 ** n) if (mask >> i) & 1]
        r = minimizar_sop(n, ms)
        for i in range(2 ** n):
            if int(any(cubo_cubre(c, i) for c in r.cobertura)) != int(i in ms):
                malas += 1
                break
        else:
            f = desde_listas(n, ms)
            if not validar(f, expresion_pos(minimizar_pos(n, ms)))["equivalente"]:
                malas += 1
    return {"n": n, "funciones": 2 ** (2 ** n), "discrepancias": malas, "segundos": round(time.perf_counter() - t0, 2)}


def algebra_vs_qm(n, muestras, semilla=2026):
    rnd = random.Random(semilla)
    ids = list(range(2 ** (2 ** n))) if muestras is None else [rnd.randrange(2 ** (2 ** n)) for _ in range(muestras)]
    iguales = peores = equiv_ok = 0
    exceso = []
    for mask in ids:
        ms = [i for i in range(2 ** n) if (mask >> i) & 1]
        if not ms:
            continue
        terms, _ = simplificar_algebraicamente(n=n, minterminos=ms)
        cub = terms_a_implicantes(terms, n)
        ok = all(int(any(cubo_cubre(c, i) for c in cub)) == int(i in ms) for i in range(2 ** n))
        equiv_ok += ok
        la = sum(literales(c, n) for c in cub)
        lq = sum(literales(c, n) for c in minimizar_sop(n, ms).cobertura)
        if la == lq:
            iguales += 1
        else:
            peores += 1
            exceso.append(la - lq)
    tot = iguales + peores
    return {"n": n, "funciones_evaluadas": tot, "equivalentes": equiv_ok, "alcanza_minimo_literales": iguales,
            "no_alcanza": peores, "exceso_medio_literales": round(sum(exceso) / len(exceso), 3) if exceso else 0,
            "exceso_max": max(exceso) if exceso else 0}


if __name__ == "__main__":
    out = {"qm_exhaustivo": [evaluar_todas(3), evaluar_todas(4)],
           "algebra_vs_qm": [algebra_vs_qm(3, None), algebra_vs_qm(4, 1500)]}
    json.dump(out, open(os.path.join(RES, "exhaustivo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
