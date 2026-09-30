"""
Algoritmo genético (GA) con representación por permutación.

Operadores (tabla del taller):
  - Selección por torneo de tamaño k: se toman k individuos al azar y gana
    el de menor costo.
  - Cruce OX (Order Crossover): el hijo copia un tramo del padre 1 y
    completa el resto con las ciudades del padre 2 EN EL ORDEN en que
    aparecen en él (así el hijo siempre es una permutación válida).
  - Mutación por inversión: se invierte un tramo al azar (equivale a 2-opt).
  - Elitismo: los 'elite' mejores pasan intactos a la siguiente generación.

FEs: cada hijo nuevo cuesta 1 evaluación. Los élites ya fueron evaluados,
así que no se vuelven a cobrar.
"""
from __future__ import annotations

import numpy as np

from .interfaz import ejecutar

PARAMETROS_DEFECTO = {
    "poblacion": 100,
    "torneo": 3,
    "prob_cruce": 0.9,
    "prob_mutacion": 0.3,
    "elite": 2,
}


def cruce_ox(p1: np.ndarray, p2: np.ndarray, rng) -> np.ndarray:
    n = len(p1)
    a, b = np.sort(rng.choice(n, size=2, replace=False))
    hijo = np.empty(n, dtype=p1.dtype)
    hijo[a:b + 1] = p1[a:b + 1]
    en_tramo = np.zeros(n, dtype=bool)
    en_tramo[p1[a:b + 1]] = True
    orden_p2 = np.roll(p2, -(b + 1))            # p2 leído desde b+1, con vuelta
    resto = orden_p2[~en_tramo[orden_p2]]
    posiciones = (b + 1 + np.arange(len(resto))) % n
    hijo[posiciones] = resto
    return hijo


def mutacion_inversion(ruta: np.ndarray, rng) -> None:
    n = len(ruta)
    a, b = np.sort(rng.choice(n, size=2, replace=False))
    ruta[a:b + 1] = ruta[a:b + 1][::-1]


def _torneo(costos, k, rng):
    candidatos = rng.integers(0, len(costos), size=k)
    return candidatos[np.argmin(costos[candidatos])]


def _nucleo(ev, rng, p):
    n = ev.n
    P, k, pc, pm, e = p["poblacion"], p["torneo"], p["prob_cruce"], p["prob_mutacion"], p["elite"]

    pob = np.array([rng.permutation(n) for _ in range(P)])
    costos = ev.evaluar_lote(pob)
    if len(costos) < P:
        return

    while True:
        orden = np.argsort(costos)
        nueva = [pob[orden[i]].copy() for i in range(e)]        # elitismo
        nuevos_costos = [costos[orden[i]] for i in range(e)]
        hijos = []
        while len(hijos) < P - e:
            p1 = pob[_torneo(costos, k, rng)]
            p2 = pob[_torneo(costos, k, rng)]
            hijo = cruce_ox(p1, p2, rng) if rng.random() < pc else p1.copy()
            if rng.random() < pm:
                mutacion_inversion(hijo, rng)
            hijos.append(hijo)
        hijos = np.array(hijos)
        c_hijos = ev.evaluar_lote(hijos)                         # P - e FEs
        if len(c_hijos) < len(hijos):
            return
        pob = np.vstack([np.array(nueva), hijos])
        costos = np.concatenate([nuevos_costos, c_hijos])


def optimizar(distancias, presupuesto, semilla, parametros=None, medir_memoria=True):
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    return ejecutar(_nucleo, distancias, presupuesto, semilla, p, medir_memoria)
