"""
Interfaz común para los cinco algoritmos (punto 1 del taller).

Cada algoritmo implementa solo su "núcleo":  nucleo(ev, rng, parametros)
El envoltorio 'ejecutar' se encarga de lo que es IGUAL para todos:
  - crear el Evaluador con el presupuesto de FEs,
  - crear el generador aleatorio con la semilla,
  - medir tiempo (time.perf_counter) y memoria pico (tracemalloc),
  - verificar la ruta y armar el diccionario de salida.
"""
from __future__ import annotations

import time
import tracemalloc

import numpy as np

from .tsp import Evaluador, PresupuestoAgotado, costo_ruta, es_ruta_valida


def ejecutar(nucleo, distancias, presupuesto, semilla, parametros, medir_memoria=True):
    rng = np.random.default_rng(semilla)
    ev = Evaluador(distancias, presupuesto)

    if medir_memoria:
        tracemalloc.start()
    t0 = time.perf_counter()
    try:
        nucleo(ev, rng, dict(parametros or {}))
    except PresupuestoAgotado:
        pass                      # forma normal de terminar: se acabó la "gasolina"
    tiempo = time.perf_counter() - t0
    memoria_mb = np.nan
    if medir_memoria:
        _, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        memoria_mb = pico / 2**20

    ruta = ev.mejor_ruta
    # Verificaciones exigidas: ruta válida y costo reportado == recalculado.
    assert es_ruta_valida(ruta, ev.n), "La ruta no es una permutación válida"
    recalculado = costo_ruta(ruta, distancias)
    assert abs(recalculado - ev.mejor_costo) < 1e-6 * max(1.0, recalculado), \
        f"Costo reportado {ev.mejor_costo} != recalculado {recalculado}"

    return {
        "mejor_ruta": ruta,
        "mejor_costo": recalculado,
        "historial": ev.historial,          # pares (evaluaciones, mejor_costo)
        "evaluaciones": ev.evaluaciones,
        "fe_mejor": ev.fe_mejor,
        "tiempo_s": tiempo,
        "memoria_mb": memoria_mb,
    }
