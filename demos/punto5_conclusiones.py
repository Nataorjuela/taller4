"""
PUNTO 5 - Análisis crítico + análisis estadístico.
Calcula, a partir de los CSV, la evidencia de cada una de las 7 preguntas y
muestra Friedman, rangos promedio y el post hoc de Wilcoxon con Holm.
"""
import _comun  # noqa: F401
from _comun import leer, titulo

df = leer("ejecuciones.csv")
df = df[df.algoritmo.isin(["GA", "ACO", "PSO", "HC", "SA"])]
ef = leer("tabla_eficiencia.csv")
rk = leer("ranking.csv")

titulo("Análisis estadístico - Friedman por tamaño")
fr = leer("friedman.csv")
fr["p_valor"] = fr["p_valor"].map(lambda p: f"{p:.1e}")
print(fr.to_string(index=False))
print("(p_valor casi 0 = las diferencias NO son casualidad)")
print("\nRangos promedio (1 = mejor):")
print(leer("rangos_promedio.csv").pivot(index="algoritmo", columns="n", values="rango_promedio").round(2).to_string())
titulo("Post hoc - Wilcoxon pareado con corrección de Holm")
ph = leer("posthoc_wilcoxon_holm.csv")
ph["p_Holm"] = ph["p_Holm"].map(lambda p: f"{p:.1e}")
print(ph[["n", "A", "B", "p_Holm", "biserial_rangos", "mejor"]].to_string(index=False))

titulo("PUNTO 5 - Evidencia para cada pregunta")
for n in (20, 50, 100):
    d = df[df.n == n]
    med = d.groupby("algoritmo")["error"].median()
    est = d.groupby(["algoritmo", "instancia"])["error"].std().groupby("algoritmo").mean()
    e = ef[ef.n == n].set_index("algoritmo")
    print(f"\n--- n = {n} ---")
    print(f"1. Menor costo (error mediano): {med.idxmin()} ({med.min():.2f} %);  más estable: {est.idxmin()} (desv {est.min():.2f})")
    llegan = d.groupby("algoritmo")["FEs_umbral"].median().dropna()
    if len(llegan):
        print(f"2. Menos FEs para error <= 1 %: {llegan.idxmin()} (mediana {llegan.min():,.0f} FEs)")
    print(f"3. Menor tiempo: {e['tiempo_medio_s'].idxmin()} ({e['tiempo_medio_s'].min():.3f} s);  "
          f"menor memoria: {e['memoria_media_MB'].idxmin()} ({e['memoria_media_MB'].min():.3f} MB)")
    orden = rk[rk.n == n].sort_values("pos_global")["algoritmo"].tolist()
    print(f"4. Ranking global: {' > '.join(orden)}")
print("""
5-7. Ver el informe (sección de conclusiones): población vs trayectoria, cuándo aceptar
     empeoramientos, y por qué NO hay un ganador absoluto (No Free Lunch).""")
