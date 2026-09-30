"""
Optimización por colonia de hormigas (ACO), variante Ant System elitista.

Cada hormiga construye una ruta paso a paso. Estando en la ciudad i, elige
la siguiente ciudad j (no visitada) con probabilidad

    P(i -> j) = [tau_ij]^alfa * [eta_ij]^beta / sum_{l no visitada} [tau_il]^alfa [eta_il]^beta

  tau_ij : feromona (memoria colectiva: "por aquí pasaron rutas buenas")
  eta_ij : visibilidad = 1 / d_ij ("lo cerca que está")

Después de que todas las hormigas terminan:
  1) Evaporación:  tau <- (1 - rho) * tau          (olvidar poco a poco)
  2) Depósito:     tau_ij += Q / L_k  por cada arista de la ruta k
                   (rutas más cortas dejan más feromona)
  3) Elitismo:     la mejor ruta histórica deposita 'elitistas' veces más.

FEs: cada ruta construida por una hormiga cuesta 1 evaluación.
"""
from __future__ import annotations

import numpy as np

from .interfaz import ejecutar

PARAMETROS_DEFECTO = {
    "hormigas": None,     # None = tantas hormigas como ciudades (m = n)
    "alfa": 1.0,
    "beta": 3.0,
    "rho": 0.1,
    "Q": 1.0,
    "elitistas": 5.0,
}


def construir_rutas(atractivo: np.ndarray, m: int, rng) -> np.ndarray:
    """Construye m rutas a la vez (vectorizado sobre las hormigas).

    Selección por ruleta: se acumulan los pesos y se lanza un número al azar
    entre 0 y la suma total; la ciudad donde "cae" es la elegida.
    """
    n = atractivo.shape[0]
    filas = np.arange(m)
    rutas = np.empty((m, n), dtype=np.int64)
    visitado = np.zeros((m, n), dtype=bool)
    actual = rng.integers(0, n, size=m)
    rutas[:, 0] = actual
    visitado[filas, actual] = True
    for paso in range(1, n):
        pesos = atractivo[actual] * ~visitado
        acumulado = np.cumsum(pesos, axis=1)
        r = rng.random(m) * acumulado[:, -1]
        siguiente = (acumulado < r[:, None]).sum(axis=1)
        siguiente = np.minimum(siguiente, n - 1)
        # Seguridad numérica: si cae en una visitada (peso 0), tomar la 1a libre
        malos = visitado[filas, siguiente]
        if malos.any():
            siguiente[malos] = np.argmax(~visitado[malos], axis=1)
        rutas[:, paso] = siguiente
        visitado[filas, siguiente] = True
        actual = siguiente
    return rutas


def _depositar(tau, rutas, costos, Q, peso=1.0):
    """Suma peso*Q/L_k en cada arista (i,j) de cada ruta k (y en (j,i)).

    Vectorizado: se convierten las aristas a índices planos i*n+j y se
    acumulan todas de una vez con np.bincount.
    """
    n = tau.shape[0]
    rutas = np.atleast_2d(np.asarray(rutas))
    sig = np.roll(rutas, -1, axis=1)
    aporte = np.repeat(peso * Q / np.asarray(costos, dtype=float), n)
    plano = np.concatenate([(rutas * n + sig).ravel(), (sig * n + rutas).ravel()])
    tau += np.bincount(plano, weights=np.tile(aporte, 2), minlength=n * n).reshape(n, n)


def _nucleo(ev, rng, p):
    n, D = ev.n, ev.D
    m = p["hormigas"] or n
    eta = 1.0 / (D + np.eye(n))                  # evita dividir por 0 en la diagonal
    np.fill_diagonal(eta, 0.0)
    # Feromona inicial tau0 = m / L0 (regla usual de Ant System), con L0 el
    # largo de una ruta de referencia (el orden 0,1,...,n-1).
    L0 = float(D[np.arange(n), np.roll(np.arange(n), -1)].sum())
    tau = np.full((n, n), m / L0)

    while True:
        atractivo = (tau ** p["alfa"]) * (eta ** p["beta"])
        rutas = construir_rutas(atractivo, m, rng)
        costos = ev.evaluar_lote(rutas)          # m FEs
        if len(costos) < m:
            return
        tau *= (1.0 - p["rho"])                  # evaporación
        _depositar(tau, rutas, costos, p["Q"])   # depósito de todas
        _depositar(tau, [ev.mejor_ruta], [ev.mejor_costo], p["Q"], p["elitistas"])
        np.fill_diagonal(tau, 0.0)


def optimizar(distancias, presupuesto, semilla, parametros=None, medir_memoria=True, guardar_rutas=False):
    p = {**PARAMETROS_DEFECTO, **(parametros or {})}
    return ejecutar(_nucleo, distancias, presupuesto, semilla, p, medir_memoria, guardar_rutas)
