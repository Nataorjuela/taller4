"""
Temple simulado (Simulated Annealing, SA) con la MISMA vecindad 2-opt de HC.

Diferencia con HC: un vecino peor (delta > 0) también se puede aceptar con
probabilidad  P = exp(-delta / T)  (criterio de Metropolis).
La temperatura T baja geométricamente: T_k = T0 * alfa^k, con alfa elegido
para que T pase de T0 a T0 * ratio_final exactamente al gastar el presupuesto.

T0 se calibra con una muestra de vecinos: se busca que un empeoramiento
típico se acepte al inicio con probabilidad p0:
    p0 = exp(-delta_medio / T0)   =>   T0 = -delta_medio / ln(p0)
"""
from __future__ import annotations

import math

from .interfaz import ejecutar
from .vecindad import Vecindad2Opt

PARAMETROS_DEFECTO = {"p0": 0.5, "ratio_final": 1e-3, "muestras_t0": 100}


def _nucleo(ev, rng, p):
    n = ev.n
    vec = Vecindad2Opt(ev.D, rng)
    ruta = rng.permutation(n).tolist()
    costo = ev.evaluar(ruta)

    # --- calibración de T0 (estas evaluaciones también cuentan como FEs) ---
    positivos = []
    for _ in range(p["muestras_t0"]):
        i, j, delta = vec.proponer(ruta)
        ev.contar_vecino(costo + delta, lambda: vec.construir(ruta, i, j))
        if delta > 0:
            positivos.append(delta)
    delta_medio = sum(positivos) / max(1, len(positivos))
    T = -delta_medio / math.log(p["p0"])
    pasos = max(1, ev.restante)
    alfa = p["ratio_final"] ** (1.0 / pasos)

    BLOQUE = 1024                     # números aleatorios pre-generados por bloques
    aleatorios, k = rng.random(BLOQUE).tolist(), 0
    while True:
        i, j, delta = vec.proponer(ruta)
        nuevo = costo + delta
        ev.contar_vecino(nuevo, lambda: vec.construir(ruta, i, j))
        if k == BLOQUE:
            aleatorios, k = rng.random(BLOQUE).tolist(), 0
        u = aleatorios[k]
        k += 1
        # Criterio de Metropolis: mejoras siempre; empeoramientos con prob. exp(-delta/T)
        if delta <= 0 or u < math.exp(-delta / T):
            vec.aplicar(ruta, i, j)
            costo = nuevo
        T *= alfa


def optimizar(distancias, presupuesto, semilla, parametros=None, medir_memoria=True):
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    return ejecutar(_nucleo, distancias, presupuesto, semilla, p, medir_memoria)
