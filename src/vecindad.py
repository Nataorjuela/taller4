"""
Generador de vecinos 2-opt COMPARTIDO por Ascenso de colinas (HC) y
Temple simulado (SA). El taller exige que ambos usen el mismo generador
para que la única diferencia entre ellos sea la regla de aceptación.

Movimiento 2-opt: se eligen dos posiciones i < j y se invierte el tramo
ruta[i..j]. Eso quita dos aristas (a,b) y (c,d) y pone (a,c) y (b,d):

    ... a -> b -> ... -> c -> d ...   ==>   ... a -> c -> ... -> b -> d ...

Cambio de costo (delta), sin recorrer toda la ruta:
    delta = d(a,c) + d(b,d) - d(a,b) - d(c,d)
"""
from __future__ import annotations

import numpy as np


class Vecindad2Opt:
    def __init__(self, D: np.ndarray, rng: np.random.Generator, bloque: int = 1024):
        self.n = D.shape[0]
        self.Dl = D.tolist()          # listas de Python: acceso escalar más rápido
        self.rng = rng
        self.bloque = bloque
        self._pares = None
        self._pos = bloque

    def _rellenar(self):
        """Pre-genera pares (i, j) con 1 <= i < j <= n-1 (la ciudad en la
        posición 0 queda fija: así cada ruta no se repite por rotación)."""
        n = self.n
        i = self.rng.integers(1, n - 1, size=self.bloque)      # 1..n-2
        u = self.rng.random(self.bloque)
        j = i + 1 + (u * (n - 1 - i)).astype(np.int64)          # i+1..n-1
        self._pares = np.stack([i, j], axis=1).tolist()
        self._pos = 0

    def proponer(self, ruta: list):
        """Devuelve (i, j, delta) de un vecino 2-opt aleatorio de 'ruta'."""
        if self._pos >= self.bloque:
            self._rellenar()
        i, j = self._pares[self._pos]
        self._pos += 1
        n, D = self.n, self.Dl
        a, b = ruta[i - 1], ruta[i]
        c, d = ruta[j], ruta[(j + 1) % n]
        delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
        return i, j, delta

    @staticmethod
    def aplicar(ruta: list, i: int, j: int) -> None:
        """Invierte ruta[i..j] en el lugar (acepta el vecino)."""
        ruta[i:j + 1] = ruta[i:j + 1][::-1]

    @staticmethod
    def construir(ruta: list, i: int, j: int) -> np.ndarray:
        """Construye el vecino SIN modificar la ruta (para guardarlo)."""
        return np.array(ruta[:i] + ruta[i:j + 1][::-1] + ruta[j + 1:])
