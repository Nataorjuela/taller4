"""
Utilidades del diseño experimental (punto 2): semillas, instancias y una
función que ejecuta UNA corrida y devuelve una fila lista para el CSV.
"""
from __future__ import annotations

import numpy as np

from . import ALGORITMOS
from .tsp import generar_ciudades, matriz_distancias


def semilla_instancia(n: int, semilla_publica: int) -> int:
    """Semilla pública de la instancia: depende solo de n y del id publicado."""
    return int(np.random.SeedSequence([semilla_publica, n]).generate_state(1)[0])


def semilla_ejecucion(maestra: int, n: int, instancia: int, repeticion: int) -> int:
    """La MISMA semilla para todos los algoritmos en (n, instancia, repetición).

    Así las comparaciones quedan "emparejadas": cada algoritmo arranca con el
    mismo generador aleatorio (útil para la prueba de Friedman).
    """
    return int(np.random.SeedSequence([maestra, n, instancia, repeticion]).generate_state(1)[0])


def crear_instancia(n: int, semilla_publica: int):
    ciudades = generar_ciudades(n, semilla_instancia(n, semilla_publica))
    return ciudades, matriz_distancias(ciudades)


def correr(tarea: dict) -> dict:
    """Ejecuta una corrida. 'tarea' trae todo lo necesario (se puede enviar
    a otro proceso). Se hacen dos pasadas con la misma semilla:
      1) sin tracemalloc -> tiempo limpio (tracemalloc hace el código más lento)
      2) con tracemalloc -> memoria pico (solo si tarea['medir_memoria'])
    Como la semilla es la misma, ambas pasadas recorren EXACTAMENTE el mismo
    camino (se verifica que el costo coincida).
    """
    _, D = crear_instancia(tarea["n"], tarea["semilla_publica"])
    f = ALGORITMOS[tarea["algoritmo"]]
    r = f(D, tarea["presupuesto"], tarea["semilla"], tarea["parametros"], medir_memoria=False)
    memoria = np.nan
    if tarea["medir_memoria"]:
        r2 = f(D, tarea["presupuesto"], tarea["semilla"], tarea["parametros"], medir_memoria=True)
        assert abs(r2["mejor_costo"] - r["mejor_costo"]) < 1e-9, "La pasada de memoria no reprodujo la corrida"
        memoria = r2["memoria_mb"]
    return {
        "algoritmo": tarea["algoritmo"],
        "n": tarea["n"],
        "instancia": tarea["instancia"],
        "repeticion": tarea["repeticion"],
        "semilla": tarea["semilla"],
        "presupuesto": tarea["presupuesto"],
        "costo": r["mejor_costo"],
        "tiempo": r["tiempo_s"],
        "memoria": memoria,
        "evaluaciones": r["evaluaciones"],
        "FEs_mejor": r["fe_mejor"],
        "ruta": " ".join(map(str, r["mejor_ruta"].tolist())),
        "historial": [(int(a), float(b)) for a, b in r["historial"]],
    }
