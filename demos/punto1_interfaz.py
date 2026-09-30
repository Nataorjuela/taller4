"""
PUNTO 1 - Interfaz común.
Corre los cinco algoritmos sobre la MISMA instancia con la MISMA firma:
    optimizar(distancias, presupuesto, semilla, parametros)
y muestra el diccionario que devuelve cada uno, las verificaciones pedidas
(ruta válida y costo reportado = recalculado), sus rutas y sus curvas.
Tarda unos 5 segundos.
"""
import _comun  # noqa: F401  (configura rutas)
from _comun import COLORES, plt, titulo

import numpy as np

from src import ALGORITMOS
from src.tsp import costo_ruta, es_ruta_valida, generar_ciudades, matriz_distancias

N, PRESUPUESTO, SEMILLA = 30, 5000, 7
ciudades = generar_ciudades(N, semilla=1)
D = matriz_distancias(ciudades)

titulo(f"PUNTO 1 - Interfaz común: {N} ciudades, presupuesto {PRESUPUESTO} FEs, semilla {SEMILLA}")

resultados = {}
for nombre in ["GA", "ACO", "PSO", "HC", "SA"]:
    r = ALGORITMOS[nombre](D, PRESUPUESTO, SEMILLA, None)      # <- la misma llamada para todos
    resultados[nombre] = r

# 1) El diccionario completo de uno de ellos
r = resultados["SA"]
print("\nEjemplo: lo que devuelve optimizar() para SA")
print("{")
print(f'  "mejor_ruta":   {r["mejor_ruta"].tolist()}')
print(f'  "mejor_costo":  {r["mejor_costo"]:.2f}')
print(f'  "historial":    [{r["historial"][0]}, {r["historial"][1]}, ... ({len(r["historial"])} pares (FEs, mejor_costo))]')
print(f'  "evaluaciones": {r["evaluaciones"]}')
print(f'  "tiempo_s":     {r["tiempo_s"]:.4f}')
print(f'  "memoria_mb":   {r["memoria_mb"]:.3f}')
print("}")

# 2) Resumen y verificaciones de los cinco
print(f"\n{'Alg.':<5}{'costo':>10}{'FEs':>8}{'FE mejor':>10}{'tiempo(s)':>11}{'mem(MB)':>9}"
      f"{'ruta válida':>13}{'costo = recalculado':>21}")
for nombre, r in resultados.items():
    valida = es_ruta_valida(r["mejor_ruta"], N)
    coincide = abs(costo_ruta(r["mejor_ruta"], D) - r["mejor_costo"]) < 1e-6
    print(f"{nombre:<5}{r['mejor_costo']:>10.2f}{r['evaluaciones']:>8}{r['fe_mejor']:>10}"
          f"{r['tiempo_s']:>11.4f}{r['memoria_mb']:>9.3f}{'sí' if valida else 'NO':>13}{'sí' if coincide else 'NO':>21}")

# 3) Gráficas: rutas y curvas de convergencia
fig, ejes = plt.subplots(2, 5, figsize=(17, 7))
fig.canvas.manager.set_window_title("Punto 1 - rutas y convergencia")
for k, (nombre, r) in enumerate(resultados.items()):
    ax = ejes[0, k]
    ruta = np.append(r["mejor_ruta"], r["mejor_ruta"][0])
    ax.plot(ciudades[ruta, 0], ciudades[ruta, 1], color=COLORES[nombre], lw=1.6)
    ax.scatter(ciudades[:, 0], ciudades[:, 1], s=14, color="black", zorder=3)
    ax.set_title(f"{nombre}: {r['mejor_costo']:.1f}")
    ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    ax2 = ejes[1, k]
    fes, costos = zip(*r["historial"])
    ax2.step(fes, costos, where="post", color=COLORES[nombre])
    ax2.set_xscale("log")
    ax2.set_xlabel("FEs (log)")
    if k == 0:
        ax2.set_ylabel("mejor costo histórico")
fig.suptitle("Arriba: mejor ruta de cada algoritmo.  Abajo: historial (FEs, mejor_costo)")
plt.tight_layout()
print("\nCierre la ventana de la gráfica para terminar.")
plt.show()
