"""
Ascenso de colinas (Hill Climbing, HC) estocástico con vecindad 2-opt.

Regla: proponer un vecino al azar; si MEJORA (delta < 0) se acepta, si no,
se descarta. Si pasan 'paciencia' propuestas seguidas sin mejora, se asume
un óptimo local y se reinicia desde una ruta aleatoria (la mejor histórica
la guarda el Evaluador, así que no se pierde).
"""
from __future__ import annotations

from .interfaz import ejecutar
from .vecindad import Vecindad2Opt

PARAMETROS_DEFECTO = {"paciencia_factor": 1.0}   # paciencia = factor * n(n-1)/2


def _nucleo(ev, rng, p):
    n = ev.n
    vec = Vecindad2Opt(ev.D, rng)
    paciencia = int(p.get("paciencia_factor", 1.0) * n * (n - 1) / 2)
    while True:
        ruta = rng.permutation(n).tolist()
        costo = ev.evaluar(ruta)                 # 1 FE: solución inicial
        sin_mejora = 0
        while sin_mejora < paciencia:
            i, j, delta = vec.proponer(ruta)
            nuevo = costo + delta
            ev.contar_vecino(nuevo, lambda: vec.construir(ruta, i, j))   # 1 FE
            if delta < -1e-12:                   # solo se aceptan mejoras
                vec.aplicar(ruta, i, j)
                costo = nuevo
                sin_mejora = 0
            else:
                sin_mejora += 1


def optimizar(distancias, presupuesto, semilla, parametros=None, medir_memoria=True, guardar_rutas=False):
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    return ejecutar(_nucleo, distancias, presupuesto, semilla, p, medir_memoria, guardar_rutas)
