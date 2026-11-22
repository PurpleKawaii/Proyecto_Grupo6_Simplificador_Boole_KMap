"""Suite de pruebas automatizadas (unittest). Ejecutar:  python -m unittest -v tests.test_simplificador"""
import os, random, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simplificador.parser_boole import (desde_listas, desde_expresion, desde_texto_listas, parsear_expresion,
                                        evaluar, asignacion, a_str)
from simplificador.algebra_boole import simplificar_algebraicamente, terms_a_implicantes
from simplificador.quine_mccluskey import (minimizar_sop, minimizar_pos, expresion_pos, cubo_a_producto,
                                           primos_implicantes, cubo_cubre)
from simplificador.kmap_visualizer import celda_de, piezas_grupo, disposicion, figura_kmap
from simplificador.validador_benchmark import (casos_obligatorios, ejecutar_caso, validar, costo_ast,
                                               ast_canonica, benchmark)


def evalua_sop(cubos, n, m):
    return any(cubo_cubre(c, m) for c in cubos)


class TestParser(unittest.TestCase):
    def test_expresion_a_minterminos(self):
        f = desde_expresion("A'B'C + A'BC + AB'C'", 3)
        self.assertEqual(sorted(f.minterminos), [1, 3, 4])

    def test_maxterminos_y_dc(self):
        f = desde_listas(3, maxterminos=[0, 1], indiferentes=[7])
        self.assertEqual(sorted(f.minterminos), [2, 3, 4, 5, 6])
        self.assertEqual(sorted(f.indiferentes), [7])

    def test_texto_listas(self):
        f = desde_texto_listas(3, "∑m(1,3) + d(7)")
        self.assertEqual((sorted(f.minterminos), sorted(f.indiferentes)), ([1, 3], [7]))

    def test_xor_y_parentesis(self):
        f = desde_expresion("(A⊕B)'", 2)
        self.assertEqual(sorted(f.minterminos), [0, 3])

    def test_rechazo_entradas_invalidas(self):
        with self.assertRaises(ValueError):
            desde_listas(3, [8])
        with self.assertRaises(ValueError):
            desde_listas(3, [1], [1])
        with self.assertRaises(ValueError):
            parsear_expresion("A + $")


class TestAlgebra(unittest.TestCase):
    def test_traza_caso1(self):
        f = desde_expresion("A'B'C + A'BC + AB'C + ABC' + ABC", 3)
        terms, traza = simplificar_algebraicamente(ast=f.ast)
        leyes = {p.ley for p in traza}
        self.assertIn("Adyacencia", leyes)
        self.assertIn("Idempotencia", leyes)
        self.assertEqual(sorted(cubo_a_producto(c, 3) for c in terms_a_implicantes(terms, 3)), ["AB", "C"])

    def test_leyes_basicas(self):
        cas = {"A + A": "A", "A(A + B)": "A", "AA'": "0", "A + 1": "1", "A·0 + B": "B",
               "(A + B)'": "A'B'", "A'' B": "AB", "AB + AB'": "A"}
        for ent, esp in cas.items():
            ast = parsear_expresion(ent)
            terms, _ = simplificar_algebraicamente(ast=ast)
            from simplificador.algebra_boole import _sop_str
            got = _sop_str(terms)
            # equivalencia semantica independiente
            n = 2
            g = parsear_expresion(got)
            e = parsear_expresion(esp)
            for i in range(4):
                self.assertEqual(evaluar(g, asignacion(i, 2)), evaluar(e, asignacion(i, 2)), (ent, got))

    def test_consenso(self):
        ast = parsear_expresion("AB + A'C + BC")
        terms, traza = simplificar_algebraicamente(ast=ast)
        self.assertIn("Consenso", [p.ley for p in traza])
        self.assertEqual(len(terms), 2)

    def test_equivalencia_aleatoria(self):
        rnd = random.Random(7)
        for _ in range(60):
            n = rnd.choice([3, 4])
            ms = [i for i in range(2 ** n) if rnd.random() < 0.5]
            if not ms:
                continue
            f = desde_listas(n, ms)
            terms, _ = simplificar_algebraicamente(n=n, minterminos=ms)
            cubos = terms_a_implicantes(terms, n)
            for i in range(2 ** n):
                self.assertEqual(int(evalua_sop(cubos, n, i)), int(i in f.minterminos))


class TestQM(unittest.TestCase):
    def test_caso_normal_3var(self):
        r = minimizar_sop(3, [1, 3, 5, 6, 7])
        self.assertEqual(r.expresion_sop(), "AB + C")

    def test_toroidal(self):
        r = minimizar_sop(4, [0, 2, 5, 7, 8, 10, 13, 15])
        self.assertEqual(r.expresion_sop(), "B'D' + BD")

    def test_dontcare_reduce(self):
        sin = minimizar_sop(4, [1, 3, 7, 11, 15])
        con = minimizar_sop(4, [1, 3, 7, 11, 15], [0, 2, 5])
        lit = lambda r: sum(4 - bin(c[1]).count("1") for c in r.cobertura)
        self.assertLess(lit(con), lit(sin))

    def test_tautologia_contradiccion(self):
        self.assertEqual(minimizar_sop(3, range(8)).expresion_sop(), "1")
        self.assertEqual(minimizar_sop(3, []).expresion_sop(), "0")
        self.assertEqual(expresion_pos(minimizar_pos(3, [])), "0")
        self.assertEqual(expresion_pos(minimizar_pos(3, range(8))), "1")

    def test_paridad_irreducible(self):
        ms = [i for i in range(16) if bin(i).count("1") % 2]
        r = minimizar_sop(4, ms)
        self.assertEqual(len(r.primos), 8)
        self.assertEqual(len(r.cobertura), 8)
        self.assertEqual(len(r.esenciales), 8)

    def test_cobertura_ciclica_petrick(self):
        r = minimizar_sop(3, [0, 1, 2, 5, 6, 7])
        self.assertEqual(len(r.primos), 6)
        self.assertEqual(r.esenciales, [])
        self.assertTrue(r.usa_petrick)
        self.assertEqual(len(r.soluciones_minimas), 2)
        self.assertEqual(len(r.cobertura), 3)

    def test_exhaustivo_n3_todas_las_funciones(self):
        """Las 256 funciones de 3 variables: SOP y POS equivalentes y minimas frente a fuerza bruta."""
        from itertools import combinations
        for mask in range(256):
            ms = [i for i in range(8) if (mask >> i) & 1]
            r = minimizar_sop(3, ms)
            for i in range(8):
                self.assertEqual(int(evalua_sop(r.cobertura, 3, i)), int(i in ms))
            # minimalidad: ninguna cobertura con menos terminos entre primos
            primos = r.primos
            mejor = None
            for k in range(0, len(primos) + 1):
                for comb in combinations(primos, k):
                    if all(any(cubo_cubre(c, m) for c in comb) for m in ms):
                        mejor = k
                        break
                if mejor is not None:
                    break
            if ms:
                self.assertEqual(len(r.cobertura), mejor, ms)

    def test_aleatorio_con_dc_n4_n5(self):
        rnd = random.Random(11)
        for n in (4, 5):
            for _ in range(60):
                u = [i for i in range(2 ** n) if rnd.random() < 0.4]
                d = [i for i in range(2 ** n) if i not in u and rnd.random() < 0.15]
                f = desde_listas(n, u, d)
                r = minimizar_sop(n, u, d)
                for i in range(2 ** n):
                    v = int(evalua_sop(r.cobertura, n, i))
                    if i in u:
                        self.assertEqual(v, 1)
                    elif i not in d:
                        self.assertEqual(v, 0)
                self.assertTrue(r.exacto)
                self.assertTrue(validar(f, r.expresion_sop())["equivalente"])
                self.assertTrue(validar(f, expresion_pos(minimizar_pos(n, u, d)))["equivalente"])


class TestKMap(unittest.TestCase):
    def test_orden_gray_4var(self):
        br, bc, of, oc = disposicion(4)
        self.assertEqual(of, [0, 1, 3, 2])
        self.assertEqual(celda_de(4, 0), (0, 0))
        self.assertEqual(celda_de(4, 10), (3, 3))

    def test_esquinas_envolventes(self):
        r = minimizar_sop(4, [0, 2, 8, 10])
        piezas, env = piezas_grupo(4, r.cobertura[0])
        self.assertTrue(env)
        self.assertEqual(len(piezas), 4)

    def test_exporta_png(self):
        ruta = os.path.join(os.path.dirname(__file__), "_tmp_kmap.png")
        r = minimizar_sop(3, [1, 3, 5, 6, 7])
        figura_kmap(ruta, 3, [1, 3, 5, 6, 7], [], r.cobertura, r.expresion_sop(), "prueba", dpi=80)
        self.assertGreater(os.path.getsize(ruta), 2000)
        os.remove(ruta)

    def test_no_soporta_5_var(self):
        with self.assertRaises(ValueError):
            disposicion(5)


class TestCasosObligatorios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = {c.id: ejecutar_caso(c, reps=2) for c in casos_obligatorios()}

    def test_todos_validan_100_por_ciento(self):
        for k, r in self.res.items():
            self.assertTrue(r["valid_sop"]["equivalente"], k)
            self.assertTrue(r["valid_pos"]["equivalente"], k)
            self.assertEqual(r["valid_sop"]["coinciden"], 2 ** r["n"], k)
            self.assertTrue(r["exacto"], k)

    def test_caso1(self):
        self.assertEqual(self.res["1"]["sop"], "AB + C")
        self.assertGreater(self.res["1"]["red_literales_sop"], 70)

    def test_caso2(self):
        self.assertEqual(self.res["2"]["sop"], "B'D' + BD")

    def test_caso3_dc(self):
        self.assertEqual(self.res["3"]["costo_sop"]["literales"], 4)

    def test_caso4_5(self):
        self.assertEqual(self.res["4"]["sop"], "1")
        self.assertEqual(self.res["5"]["sop"], "0")
        self.assertEqual(self.res["5"]["pos"], "0")

    def test_caso6_paridad_cero_reduccion(self):
        self.assertEqual(self.res["6"]["red_literales_sop"], 0.0)
        self.assertEqual(self.res["6"]["num_esenciales"], 8)

    def test_caso7_petrick(self):
        self.assertTrue(self.res["7"]["usa_petrick"])
        self.assertEqual(self.res["7"]["num_esenciales"], 0)

    def test_caso8_escalabilidad(self):
        self.assertEqual(self.res["8a"]["n"], 5)
        self.assertEqual(self.res["8b"]["n"], 6)
        self.assertLess(self.res["8b"]["costo_sop"]["literales"], self.res["8b"]["costo_original"]["literales"])

    def test_benchmark_pequeno(self):
        b = benchmark(semilla=1, instancias={2: 5, 3: 5, 4: 5, 5: 3, 6: 2}, iter_peor={2: 5, 3: 5, 4: 5, 5: 5, 6: 5})
        self.assertEqual([r["n"] for r in b], [2, 3, 4, 5, 6])
        self.assertTrue(all(r["primos_paridad"] == 2 ** (r["n"] - 1) for r in b))


if __name__ == "__main__":
    unittest.main(verbosity=2)
