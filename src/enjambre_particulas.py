"""
Optimización por enjambre de partículas (PSO) con CLAVES ALEATORIAS.

PSO trabaja en el espacio continuo, pero una ruta es discreta. Truco de las
"random keys": cada partícula es un vector x en R^n; la ruta se obtiene
ORDENANDO las claves:  ruta = argsort(x).
  Ejemplo: x = [0.7, 0.1, 0.4]  ->  argsort = [1, 2, 0]  ->  ruta 1 -> 2 -> 0

Actualización (PSO clásico con peso de inercia w):
    v <- w v + c1 r1 (pbest - x) + c2 r2 (gbest - x)
    x <- x + v
  pbest: mejor posición que ha visto ESA partícula (memoria personal)
  gbest: mejor posición de TODO el enjambre (memoria social)
  r1, r2 ~ U(0,1) componente a componente.

FEs: cada partícula evaluada en cada iteración cuesta 1 evaluación.
"""
from __future__ import annotations

import numpy as np

from .interfaz import ejecutar

PARAMETROS_DEFECTO = {
    "particulas": 50,
    "w": 0.729,          # coeficientes de "constricción" de Clerc y Kennedy
    "c1": 1.49445,
    "c2": 1.49445,
    "vmax": 0.5,
}


def decodificar(X: np.ndarray) -> np.ndarray:
    return np.argsort(X, axis=1)


def _nucleo(ev, rng, p):
    n, S = ev.n, p["particulas"]
    X = rng.random((S, n))
    V = rng.uniform(-p["vmax"], p["vmax"], size=(S, n))
    costos = ev.evaluar_lote(decodificar(X))
    if len(costos) < S:
        return
    pbest, pbest_c = X.copy(), costos.copy()
    g = int(np.argmin(pbest_c))

    while True:
        r1, r2 = rng.random((S, n)), rng.random((S, n))
        V = p["w"] * V + p["c1"] * r1 * (pbest - X) + p["c2"] * r2 * (pbest[g] - X)
        np.clip(V, -p["vmax"], p["vmax"], out=V)
        X = X + V
        costos = ev.evaluar_lote(decodificar(X))           # S FEs
        k = len(costos)
        mejora = costos < pbest_c[:k]
        idx = np.nonzero(mejora)[0]
        pbest[idx], pbest_c[idx] = X[idx], costos[idx]
        g = int(np.argmin(pbest_c))
        if k < S:
            return


def optimizar(distancias, presupuesto, semilla, parametros=None, medir_memoria=True, guardar_rutas=False):
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    return ejecutar(_nucleo, distancias, presupuesto, semilla, p, medir_memoria, guardar_rutas)
