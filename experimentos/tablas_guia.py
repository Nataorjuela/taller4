"""Genera las tablas LaTeX que usan la guía y el informe (a partir de los CSV)."""
import os, sys
import numpy as np, pandas as pd
R = os.path.join(os.path.dirname(__file__), "..", "resultados")
S = os.path.join(os.path.dirname(__file__), "..", "guia", "tablas")
os.makedirs(S, exist_ok=True)
ALGS = ["GA", "ACO", "PSO", "HC", "SA"]
f = lambda x, d=2: "--" if pd.isna(x) else f"{x:,.{d}f}".replace(",", "X").replace(".", "{,}").replace("X", "\\,")

def escribir(nombre, cab, filas, alin, agrupar=True):
    L = ["\\begin{tabular}{" + alin + "}", "\\toprule", " & ".join(cab) + " \\\\", "\\midrule"]
    prev = None
    for fl in filas:
        if agrupar and prev is not None and fl[0] != prev and fl[0] != "":
            L.append("\\midrule")
        prev = fl[0] if fl[0] != "" else prev
        L.append(" & ".join(fl) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(S, nombre + ".tex"), "w").write("\n".join(L) + "\n")

d = pd.read_csv(os.path.join(R, "ejecuciones.csv"))
d = d[d.algoritmo.isin(ALGS)]
ef = pd.read_csv(os.path.join(R, "tabla_eficiencia.csv"))
rend = pd.read_csv(os.path.join(R, "tabla_rendimiento.csv"))
estab = d.groupby(["n", "algoritmo", "instancia"])["error"].std().groupby(["n", "algoritmo"]).mean()

# --- Eficiencia (punto 3)
filas = []
for n in (20, 50, 100):
    for a in ALGS:
        e = ef[(ef.n == n) & (ef.algoritmo == a)].iloc[0]
        alc = d[(d.n == n) & (d.algoritmo == a)]["FEs_umbral"].notna().sum()
        filas.append([str(n) if a == "GA" else "", a, f(e.tiempo_medio_s, 3), f(e.tiempo_por_1000FEs_ms, 1),
                      f(e.memoria_media_MB, 3), f(e.exito_pct, 1),
                      f(e.FEs_umbral_mediana, 0) if alc else "--", f"{alc}/150"])
escribir("eficiencia", ["$n$", "Alg.", "tiempo (s)", "ms/1000 FEs", "memoria (MB)", "éxito (\\%)", "FEs al 1\\% (med.)", "llegaron"], filas, "clrrrrrr")

# --- Rendimiento (punto 4c)
filas = []
for n in (20, 50, 100):
    for a in ALGS:
        g = d[(d.n == n) & (d.algoritmo == a)]["error"]
        r = rend[(rend.n == n) & (rend.algoritmo == a)].iloc[0]
        filas.append([str(n) if a == "GA" else "", a, f(g.min()), f(g.mean()), f(g.median()), f(estab[(n, a)]),
                      f(g.quantile(.75) - g.quantile(.25)), f(r["exito_%"], 1), f(r["mejora_%"], 1)])
escribir("rendimiento", ["$n$", "Alg.", "mejor", "media", "mediana", "desv.$^\\dagger$", "RIC", "éxito (\\%)", "mejora (\\%)"], filas, "clrrrrrrr")

# --- Costos absolutos en la instancia 0 de cada tamaño
filas = []
for n in (20, 50, 100):
    for a in ALGS:
        g = d[(d.n == n) & (d.algoritmo == a) & (d.instancia == 0)]["costo"]
        filas.append([str(n) if a == "GA" else "", a, f(g.min()), f(g.mean()), f(g.median()), f(g.std())])
escribir("costos_inst0", ["$n$", "Alg.", "mejor", "media", "mediana", "desv."], filas, "clrrrr")

# --- Friedman
fr = pd.read_csv(os.path.join(R, "friedman.csv")); rk = pd.read_csv(os.path.join(R, "rangos_promedio.csv"))
filas = []
for _, x in fr.iterrows():
    rr = rk[rk.n == x.n].set_index("algoritmo")["rango_promedio"]
    p = "$<10^{-16}$" if x.p_valor < 1e-16 else f"{x.p_valor:.1e}"
    filas.append([str(int(x.n)), f(x.chi2, 1), p, f(x.W_Kendall, 3)] + [f(rr[a]) for a in ALGS])
escribir("friedman", ["$n$", "$\\chi^2_F$", "$p$", "$W$"] + [f"$\\bar R$ {a}" for a in ALGS], filas, "rrrr" + "r" * 5)

# --- Post hoc (compacto)
ph = pd.read_csv(os.path.join(R, "posthoc_wilcoxon_holm.csv"))
filas = []
for (a, b), g in ph.groupby(["A", "B"], sort=False):
    fila = [f"{a} vs {b}", ""]
    for n in (20, 50, 100):
        x = g[g.n == n].iloc[0]
        p = "$<10^{-4}$" if x.p_Holm < 1e-4 else f(x.p_Holm, 4)
        fila.append(f"{x.mejor} ({f(x.biserial_rangos).replace('-', '$-$')}; {p})")
    filas.append(fila)
for fl in filas: fl.pop(1)
escribir("posthoc", ["Par", "$n=20$", "$n=50$", "$n=100$"], filas, "llll", agrupar=False)

# --- Ranking
rkg = pd.read_csv(os.path.join(R, "ranking.csv"))
filas = []
for n in (20, 50, 100):
    for i, (_, x) in enumerate(rkg[rkg.n == n].iterrows()):
        filas.append([str(n) if i == 0 else "", x.algoritmo, str(x.pos_calidad), str(x.pos_estabilidad), str(x.pos_velocidad),
                      f"\\textbf{{{x.pos_global}}}", f(x["calidad (rango Friedman)"]), f(x["estabilidad (desv. error %)"]), f(x["velocidad (AUC error)"], 1)])
escribir("ranking", ["$n$", "Alg.", "calidad", "estab.", "veloc.", "global", "$\\bar R$", "desv. error", "AUC"], filas, "clccccrrr")

# --- Híbrido
hb = pd.read_csv(os.path.join(R, "hibrido.csv")); dt = pd.read_csv(os.path.join(R, "ejecuciones.csv"))
filas = []
for n in (20, 50, 100):
    for i, (_, x) in enumerate(hb[hb.n == n].iterrows()):
        p = "$<10^{-4}$" if x.p_Holm < 1e-4 else f(x.p_Holm, 3)
        filas.append([str(n) if i == 0 else "", x.contra, f(x.error_mediana_hibrido), f(x.error_mediana_contra), f(x["gana_hibrido_%"], 1), p])
escribir("hibrido", ["$n$", "vs.", "err. med. híbrido", "err. med. rival", "gana híbrido (\\%)", "$p$ Holm"], filas, "clrrrr")
print("tablas listas en", S)
