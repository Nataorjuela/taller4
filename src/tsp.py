"""
Herramientas comunes del problema del viajante (TSP).

Todo lo que comparten los cinco algoritmos vive aquí:
  - generación de instancias con semillas públicas,
  - matriz de distancias euclidianas,
  - función objetivo f(pi) (ecuación 1 del taller),
  - el "Evaluador": cuenta evaluaciones (FEs), guarda la mejor solución
    histórica y el historial (FEs, mejor_costo).

La idea clave: NINGÚN algoritmo calcula el costo por su cuenta. Todos le
piden al Evaluador que lo haga, así el conteo de FEs es idéntico para todos.
"""
from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Instancias
# ---------------------------------------------------------------------------
def generar_ciudades(n: int, semilla: int) -> np.ndarray:
    """n ciudades con coordenadas uniformes en [0,100] x [0,100]."""
    rng = np.random.default_rng(semilla)
    return rng.uniform(0.0, 100.0, size=(n, 2))


def matriz_distancias(ciudades: np.ndarray) -> np.ndarray:
    """d_ij = sqrt((x_i-x_j)^2 + (y_i-y_j)^2), calculada de forma vectorizada."""
    dif = ciudades[:, None, :] - ciudades[None, :, :]
    return np.sqrt((dif ** 2).sum(axis=-1))


# ---------------------------------------------------------------------------
# Función objetivo
# ---------------------------------------------------------------------------
def costo_ruta(ruta: np.ndarray, D: np.ndarray) -> float:
    """f(pi) = sum_{k=1}^{n-1} d(pi_k, pi_{k+1}) + d(pi_n, pi_1).

    np.roll(ruta, -1) es la ruta "corrida" una posición: emparejar ruta con
    su versión corrida da exactamente todos los tramos, incluido el regreso.
    """
    ruta = np.asarray(ruta)
    return float(D[ruta, np.roll(ruta, -1)].sum())


def costos_lote(rutas: np.ndarray, D: np.ndarray) -> np.ndarray:
    """Costo de varias rutas a la vez (una ruta por fila)."""
    return D[rutas, np.roll(rutas, -1, axis=1)].sum(axis=1)


def es_ruta_valida(ruta, n: int) -> bool:
    """Una ruta es válida si es una permutación de 0..n-1 (cada ciudad 1 vez)."""
    ruta = np.asarray(ruta)
    return ruta.shape == (n,) and np.array_equal(np.sort(ruta), np.arange(n))


# ---------------------------------------------------------------------------
# Evaluador: el "contador de gasolina" compartido
# ---------------------------------------------------------------------------
class PresupuestoAgotado(Exception):
    """Se lanza cuando un algoritmo intenta evaluar sin presupuesto."""


class Evaluador:
    """Cuenta FEs y recuerda la mejor solución histórica.

    historial: lista de pares (evaluaciones, mejor_costo) que se agrega
    cada vez que el mejor costo mejora (curva escalonada de convergencia).
    """

    def __init__(self, D: np.ndarray, presupuesto: int, guardar_rutas: bool = False):
        self.D = D
        self.n = D.shape[0]
        self.presupuesto = int(presupuesto)
        self.evaluaciones = 0
        self.mejor_costo = np.inf
        self.mejor_ruta = None
        self.fe_mejor = 0
        self.historial: list[tuple[int, float]] = []
        # Opcional (interfaz gráfica): copia de la ruta en cada mejora, para animarla
        self.guardar_rutas = guardar_rutas
        self.rutas_historial: list[tuple[int, float, list]] = []

    # --- utilidades ---------------------------------------------------------
    @property
    def restante(self) -> int:
        return self.presupuesto - self.evaluaciones

    def agotado(self) -> bool:
        return self.evaluaciones >= self.presupuesto

    def _registrar(self, costo: float, ruta) -> None:
        if costo < self.mejor_costo - 1e-12:
            self.mejor_costo = float(costo)
            self.mejor_ruta = np.array(ruta, copy=True)
            self.fe_mejor = self.evaluaciones
            self.historial.append((self.evaluaciones, self.mejor_costo))
            if self.guardar_rutas:
                self.rutas_historial.append((self.evaluaciones, self.mejor_costo, self.mejor_ruta.tolist()))

    # --- evaluación completa (O(n)) ----------------------------------------
    def evaluar(self, ruta) -> float:
        if self.agotado():
            raise PresupuestoAgotado
        self.evaluaciones += 1
        c = costo_ruta(ruta, self.D)
        self._registrar(c, ruta)
        return c

    def evaluar_lote(self, rutas: np.ndarray) -> np.ndarray:
        """Evalúa hasta 'restante' rutas; devuelve solo los costos evaluados.

        Si el presupuesto no alcanza para todo el lote, se evalúan las
        primeras k rutas y el algoritmo debe detenerse.
        """
        k = min(len(rutas), self.restante)
        if k <= 0:
            raise PresupuestoAgotado
        costos = costos_lote(rutas[:k], self.D)
        # Registrar en orden para que el historial tenga el FE exacto.
        base = self.evaluaciones
        mejor_prev = self.mejor_costo
        idx_min = int(np.argmin(costos))
        if costos[idx_min] < mejor_prev - 1e-12:
            # Recorremos solo si hubo mejora, para registrar cada escalón.
            for i in range(k):
                self.evaluaciones = base + i + 1
                self._registrar(costos[i], rutas[i])
        self.evaluaciones = base + k
        return costos

    # --- evaluación incremental (2-opt, O(1)) ------------------------------
    def contar_vecino(self, costo_vecino: float, ruta_si_mejora=None) -> None:
        """Cuenta 1 FE para un vecino evaluado con la fórmula delta.

        La fórmula delta da EXACTAMENTE el mismo número que recalcular f
        completa, pero en O(1). Contarla como 1 FE es justo: el algoritmo
        "consultó" la calidad de una solución candidata.
        'ruta_si_mejora' es una función que construye la ruta solo si hace
        falta guardarla (evita copiar la ruta en cada paso).
        """
        if self.agotado():
            raise PresupuestoAgotado
        self.evaluaciones += 1
        if costo_vecino < self.mejor_costo - 1e-12:
            self._registrar(costo_vecino, ruta_si_mejora())


# ---------------------------------------------------------------------------
# Curvas: mejor costo histórico en puntos fijos del presupuesto
# ---------------------------------------------------------------------------
def mejor_en_puntos(historial, puntos_fe) -> np.ndarray:
    """Evalúa la curva escalonada del historial en los FEs pedidos.

    Así todas las ejecuciones quedan en el MISMO eje de FEs y se pueden
    promediar (lo exige el punto 4 del taller).
    """
    fes = np.array([h[0] for h in historial])
    val = np.array([h[1] for h in historial])
    idx = np.searchsorted(fes, puntos_fe, side="right") - 1
    salida = np.where(idx >= 0, val[np.clip(idx, 0, None)], np.nan)
    return salida
