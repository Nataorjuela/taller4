"""
PUNTO 4 - Rendimiento, convergencia y estabilidad.
Muestra la tabla de rendimiento, el ranking y las gráficas: convergencia (a),
cajas (b), rutas (d).
"""
import _comun  # noqa: F401
from _comun import leer, mostrar_figuras, titulo

rend = leer("tabla_rendimiento.csv")
titulo("PUNTO 4 (c) - Error relativo final (%): media, mediana, desviación, mejor, éxito")
print(rend[["n", "algoritmo", "error_medio_%", "error_mediana_%", "IQR_error", "exito_%", "mejora_%"]].to_string(index=False))

inst = leer("tabla_rendimiento_por_instancia.csv")
titulo("Costo absoluto en la instancia 0 (mejor, media, mediana, desviación)")
print(inst[inst.instancia == 0][["n", "algoritmo", "mejor", "media", "mediana", "desv"]].to_string(index=False))

rk = leer("ranking.csv")
titulo("PUNTO 4 (e) - Ranking por calidad, estabilidad y velocidad (1 = mejor)")
print(rk[["n", "algoritmo", "pos_calidad", "pos_estabilidad", "pos_velocidad", "pos_global"]].to_string(index=False))

mostrar_figuras(["fig4a_convergencia", "fig4b_cajas_error", "fig4d_rutas"], "Punto 4")
