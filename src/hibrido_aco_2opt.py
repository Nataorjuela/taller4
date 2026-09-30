"""
Híbrido ACO + mejora local 2-opt (pregunta de profundización opcional).

Idea: ACO es bueno "explorando" (decide QUÉ zonas del espacio visitar gracias
a la feromona), y 2-opt es bueno "explotando" (pule una ruta hasta que no
tenga cruces). En cada iteración:
  1) la colonia construye m rutas (m FEs),
  2) la MEJOR ruta de la iteración se pule con 'pasos_ls' propuestas 2-opt
     de ascenso de colinas (cada propuesta = 1 FE, la misma vecindad de HC/SA),
  3) la feromona se actualiza usando la ruta ya pulida.
El presupuesto TOTAL de FEs es el mismo que el de los demás algoritmos.
"""
from __future__ import annotations

import numpy as np

from .colonia_hormigas import PARAMETROS_DEFECTO as P_ACO
from .colonia_hormigas import _depositar, construir_rutas
from .interfaz import ejecutar
from .vecindad import Vecindad2Opt

PARAMETROS_DEFECTO = {**P_ACO, "pasos_ls_factor": 5}     # pasos_ls = factor * n


def _nucleo(ev, rng, p):
    n, D = ev.n, ev.D
    m = p["hormigas"] or n
    vec = Vecindad2Opt(D, rng)
    pasos_ls = int(p["pasos_ls_factor"] * n)
    eta = 1.0 / (D + np.eye(n))
    np.fill_diagonal(eta, 0.0)
    L0 = float(D[np.arange(n), np.roll(np.arange(n), -1)].sum())
    tau = np.full((n, n), m / L0)

    while True:
        atractivo = (tau ** p["alfa"]) * (eta ** p["beta"])
        rutas = construir_rutas(atractivo, m, rng)
        costos = ev.evaluar_lote(rutas)
        if len(costos) < m:
            return
        # --- mejora local 2-opt sobre la mejor hormiga de la iteración ---
        b = int(np.argmin(costos))
        ruta, costo = rutas[b].tolist(), float(costos[b])
        for _ in range(pasos_ls):
            i, j, delta = vec.proponer(ruta)
            ev.contar_vecino(costo + delta, lambda: vec.construir(ruta, i, j))
            if delta < -1e-12:
                vec.aplicar(ruta, i, j)
                costo += delta
        rutas[b], costos[b] = np.array(ruta), costo
        # --- actualización de feromona ---
        tau *= (1.0 - p["rho"])
        _depositar(tau, rutas, costos, p["Q"])
        _depositar(tau, [ev.mejor_ruta], [ev.mejor_costo], p["Q"], p["elitistas"])
        np.fill_diagonal(tau, 0.0)


def optimizar(distancias, presupuesto, semilla, parametros=None, medir_memoria=True, guardar_rutas=False):
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    return ejecutar(_nucleo, distancias, presupuesto, semilla, p, medir_memoria, guardar_rutas)
