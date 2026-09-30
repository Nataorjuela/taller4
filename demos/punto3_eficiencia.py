"""
PUNTO 3 - Eficiencia computacional y escalabilidad.
Lee los resultados oficiales y muestra: tabla de tiempo, memoria, tasa de éxito
y FEs para llegar al 1 %, y las gráficas de tiempo/memoria/error frente a n.
"""
import _comun  # noqa: F401
from _comun import leer, mostrar_figuras, titulo

ef = leer("tabla_eficiencia.csv")
titulo("PUNTO 3 (a, b, c) - Tiempo, memoria, éxito y FEs necesarias para error <= 1 %")
print(ef[["n", "algoritmo", "tiempo_medio_s", "tiempo_por_1000FEs_ms", "memoria_media_MB",
          "exito_pct", "FEs_umbral_mediana"]].to_string(index=False))

titulo("PUNTO 3 (d) - ¿Quién escala mejor?")
t = ef.pivot(index="algoritmo", columns="n", values="tiempo_por_1000FEs_ms")
t["crecimiento 20->100"] = t[100] / t[20]
print("Milisegundos por cada 1000 FEs (si casi no crece, escala bien en tiempo):")
print(t.round(2).to_string())
e = leer("tabla_rendimiento.csv").pivot(index="algoritmo", columns="n", values="error_mediana_%")
print("\nError mediano (%) (si crece poco, escala bien en calidad):")
print(e.round(2).to_string())
print("\n-> En tiempo escalan mejor HC y SA; en calidad escala mejor ACO.")

mostrar_figuras(["fig3a_tiempo_vs_n", "fig3b_memoria_vs_n", "fig3d_error_vs_n"], "Punto 3")
