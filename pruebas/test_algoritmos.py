"""
Pruebas automáticas (punto 1): ejecutar con   python -m pytest pruebas -q
o directamente:                               python pruebas/test_algoritmos.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import ALGORITMOS                                   # noqa: E402
from src.genetico import cruce_ox                            # noqa: E402
from src.tsp import (Evaluador, costo_ruta, es_ruta_valida,  # noqa: E402
                     generar_ciudades, matriz_distancias)
from src.vecindad import Vecindad2Opt                        # noqa: E402


def _instancia(n=20, semilla=123):
    return matriz_distancias(generar_ciudades(n, semilla))


def test_costo_manual():
    # Cuadrado de lado 1: la ruta 0-1-2-3 mide 4.
    ciudades = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    D = matriz_distancias(ciudades)
    assert abs(costo_ruta([0, 1, 2, 3], D) - 4.0) < 1e-12
    assert abs(costo_ruta([0, 2, 1, 3], D) - (2 + 2 * np.sqrt(2))) < 1e-12


def test_delta_2opt_igual_a_recalcular():
    D = _instancia(30)
    rng = np.random.default_rng(0)
    vec = Vecindad2Opt(D, rng)
    ruta = rng.permutation(30).tolist()
    for _ in range(2000):
        i, j, delta = vec.proponer(ruta)
        vecino = vec.construir(ruta, i, j)
        assert es_ruta_valida(vecino, 30)
        assert abs((costo_ruta(vecino, D) - costo_ruta(ruta, D)) - delta) < 1e-9
        if delta < 0:
            vec.aplicar(ruta, i, j)


def test_cruce_ox_produce_permutaciones():
    rng = np.random.default_rng(1)
    for _ in range(500):
        p1, p2 = rng.permutation(25), rng.permutation(25)
        assert es_ruta_valida(cruce_ox(p1, p2, rng), 25)


def test_todos_los_algoritmos():
    """Ruta válida, costo reportado = recalculado, presupuesto exacto."""
    D = _instancia(20)
    for nombre, f in ALGORITMOS.items():
        r = f(D, 2000, 42, None, medir_memoria=False)
        assert es_ruta_valida(r["mejor_ruta"], 20), nombre
        assert abs(costo_ruta(r["mejor_ruta"], D) - r["mejor_costo"]) < 1e-6, nombre
        assert r["evaluaciones"] == 2000, nombre
        costos = [c for _, c in r["historial"]]
        assert all(a >= b for a, b in zip(costos, costos[1:])), nombre   # no empeora
        assert abs(costos[-1] - r["mejor_costo"]) < 1e-6, nombre


def test_reproducibilidad():
    D = _instancia(20)
    for nombre, f in ALGORITMOS.items():
        a = f(D, 1500, 7, None, medir_memoria=False)
        b = f(D, 1500, 7, None, medir_memoria=False)
        assert a["mejor_costo"] == b["mejor_costo"], nombre
        assert np.array_equal(a["mejor_ruta"], b["mejor_ruta"]), nombre


def test_evaluador_no_se_pasa_del_presupuesto():
    D = _instancia(10)
    ev = Evaluador(D, 5)
    rutas = np.array([np.random.default_rng(i).permutation(10) for i in range(8)])
    assert len(ev.evaluar_lote(rutas)) == 5 and ev.evaluaciones == 5


if __name__ == "__main__":
    for nombre, prueba in list(globals().items()):
        if nombre.startswith("test_"):
            prueba()
            print("OK", nombre)
