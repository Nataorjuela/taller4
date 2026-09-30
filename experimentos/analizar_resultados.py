"""
Análisis de resultados (puntos 3, 4 y 5 + análisis estadístico + híbrido).

Uso:  python experimentos/analizar_resultados.py --config configuracion.json

Lee resultados/ejecuciones.csv y resultados/corridas.jsonl y produce:
  figuras/  -> gráficas PNG (y PDF) con título, unidades y leyenda
  resultados/ -> tablas resumidas en CSV y en LaTeX (.tex)
"""
import argparse
import json
import os
import sys
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ)
from src.tsp import mejor_en_puntos  # noqa: E402

# Colores fijos por algoritmo (el color sigue a la entidad, nunca al ranking)
COLORES = {"GA": "#2a78d6", "ACO": "#eb6834", "PSO": "#1baf7a", "HC": "#eda100",
           "SA": "#e87ba4", "ACO+2opt": "#008300"}
MARCAS = {"GA": "o", "ACO": "s", "PSO": "^", "HC": "D", "SA": "v", "ACO+2opt": "P"}
TINTA, TINTA2, REJILLA = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 200, "font.size": 10, "axes.titlesize": 11,
    "axes.edgecolor": TINTA2, "axes.labelcolor": TINTA, "xtick.color": TINTA2,
    "ytick.color": TINTA2, "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.7,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "lines.linewidth": 2.0,
})


def ticks_legibles(ax, eje="y"):
    """Números normales (0, 1, 10, 100) en vez de notación 10^k."""
    from matplotlib.ticker import FuncFormatter
    fmt = FuncFormatter(lambda v, _: f"{v:g}")
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(fmt)


def etiquetas_sin_choque(ax, puntos, log=True, sep=0.11):
    """Etiqueta al final de cada línea, separando verticalmente las que chocan.
    puntos: lista de (texto, x, y)."""
    import math
    pts = sorted(puntos, key=lambda t: t[2])
    pos = [math.log10(y) if log else y for _, _, y in pts]
    rango = (max(pos) - min(pos)) or 1.0
    minimo = sep * rango
    for i in range(1, len(pos)):
        if pos[i] - pos[i - 1] < minimo:
            pos[i] = pos[i - 1] + minimo
    for (txt, x, _), p in zip(pts, pos):
        ax.annotate(txt, (x, 10 ** p if log else p), xytext=(8, 0), textcoords="offset points",
                    va="center", color=TINTA2, fontsize=9)


def guardar(fig, carpeta, nombre):
    fig.tight_layout()
    fig.savefig(os.path.join(carpeta, nombre + ".png"), bbox_inches="tight")
    fig.savefig(os.path.join(carpeta, nombre + ".pdf"), bbox_inches="tight")
    plt.close(fig)


def tabla_latex(df, archivo, formatos=None, titulo=None):
    """Escribe una tabla booktabs sencilla para pegar en el informe."""
    formatos = formatos or {}
    cols = list(df.columns)
    lineas = ["\\begin{tabular}{" + "l" * 2 + "r" * (len(cols) - 2) + "}", "\\toprule",
              " & ".join(str(c).replace("_", "\\_").replace("%", "\\%") for c in cols) + " \\\\", "\\midrule"]
    previo = None
    for _, fila in df.iterrows():
        if previo is not None and fila[cols[0]] != previo:
            lineas.append("\\midrule")
        previo = fila[cols[0]]
        celdas = []
        for c in cols:
            v = fila[c]
            if isinstance(v, (int, np.integer)):
                v = float(v)
            if isinstance(v, (float, np.floating)):
                fmt = formatos.get(c, "{:.2f}")
                if np.isnan(v):
                    celdas.append("--")
                else:
                    celdas.append(fmt.format(int(round(v))) if "d}" in fmt else fmt.format(v))
            else:
                celdas.append(str(v).replace("_", "\\_").replace("%", "\\%"))
        lineas.append(" & ".join(celdas) + " \\\\")
    lineas += ["\\bottomrule", "\\end{tabular}"]
    with open(archivo, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def holm(pvalores):
    """Corrección de Holm: ordena p de menor a mayor y multiplica por (m - i)."""
    p = np.asarray(pvalores, dtype=float)
    m = len(p)
    orden = np.argsort(p)
    ajust = np.empty(m)
    maximo = 0.0
    for i, k in enumerate(orden):
        maximo = max(maximo, min(1.0, (m - i) * p[k]))
        ajust[k] = maximo
    return ajust


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configuracion.json")
    cfg = json.load(open(ap.parse_args().config, encoding="utf-8"))
    RES = os.path.join(RAIZ, cfg["carpeta_resultados"])
    FIG = os.path.join(RAIZ, cfg["carpeta_figuras"])
    os.makedirs(FIG, exist_ok=True)
    ALGS = cfg["algoritmos"]
    EXTRA = cfg.get("algoritmos_extra", [])
    NS = sorted(cfg["tamanos"])
    eps_pct = 100 * cfg["epsilon"]

    df_todo = pd.read_csv(os.path.join(RES, "ejecuciones.csv"))
    df = df_todo[df_todo["algoritmo"].isin(ALGS)].copy()
    df["exito"] = df["error"] <= eps_pct + 1e-9

    # =====================================================================
    # PUNTO 4c: tabla de rendimiento
    # =====================================================================
    def resumen(g):
        return pd.Series({
            "mejor": g["costo"].min(), "media": g["costo"].mean(), "mediana": g["costo"].median(),
            "desv": g["costo"].std(ddof=1),
            "error_medio_%": g["error"].mean(), "error_mediana_%": g["error"].median(),
            "IQR_error": g["error"].quantile(0.75) - g["error"].quantile(0.25),
            "exito_%": 100 * g["exito"].mean(),
            "mejora_%": g["mejora"].mean(),
        })
    tab = (df.groupby(["n", "algoritmo"]).apply(resumen, include_groups=False).reset_index())
    tab["algoritmo"] = pd.Categorical(tab["algoritmo"], ALGS)
    tab = tab.sort_values(["n", "algoritmo"])
    tab.to_csv(os.path.join(RES, "tabla_rendimiento.csv"), index=False)
    tabla_latex(tab, os.path.join(RES, "tabla_rendimiento.tex"),
                {"exito_%": "{:.1f}", "n": "{:d}", "mejora_%": "{:.1f}"})

    # Misma tabla POR INSTANCIA (el costo solo es comparable dentro de una instancia)
    tab_inst = (df.groupby(["n", "instancia", "algoritmo"]).apply(resumen, include_groups=False).reset_index())
    tab_inst["algoritmo"] = pd.Categorical(tab_inst["algoritmo"], ALGS)
    tab_inst.sort_values(["n", "instancia", "algoritmo"]).to_csv(
        os.path.join(RES, "tabla_rendimiento_por_instancia.csv"), index=False)

    # Desviación del costo DENTRO de cada instancia (estabilidad sin mezclar
    # instancias de distinto tamaño de ruta) -> se promedia sobre instancias
    estab = (df.groupby(["n", "algoritmo", "instancia"])["error"].std(ddof=1)
               .groupby(["n", "algoritmo"]).mean().rename("desv_error_intra_instancia"))

    # =====================================================================
    # PUNTO 3: eficiencia y escalabilidad
    # =====================================================================
    efic = df.groupby(["n", "algoritmo"]).agg(
        tiempo_medio_s=("tiempo", "mean"), tiempo_desv_s=("tiempo", "std"),
        tiempo_por_1000FEs_ms=("tiempo_por_1000FEs", lambda s: 1000 * s.mean()),
        memoria_media_MB=("memoria", "mean"), memoria_desv_MB=("memoria", "std"),
        exito_pct=("exito", lambda s: 100 * s.mean()),
        FEs_umbral_mediana=("FEs_umbral", "median"),
        FEs_umbral_media=("FEs_umbral", "mean"),
    ).reset_index()
    efic["FEs_umbral_%presupuesto"] = 100 * efic["FEs_umbral_mediana"] / efic["n"].map(
        lambda n: cfg["presupuestos"][str(n)])
    efic["algoritmo"] = pd.Categorical(efic["algoritmo"], ALGS)
    efic = efic.sort_values(["n", "algoritmo"])
    efic.to_csv(os.path.join(RES, "tabla_eficiencia.csv"), index=False)
    t3 = efic[["n", "algoritmo", "tiempo_medio_s", "tiempo_por_1000FEs_ms", "memoria_media_MB",
               "exito_pct", "FEs_umbral_mediana", "FEs_umbral_%presupuesto"]]
    tabla_latex(t3, os.path.join(RES, "tabla_eficiencia.tex"),
                {"tiempo_medio_s": "{:.3f}", "tiempo_por_1000FEs_ms": "{:.2f}",
                 "memoria_media_MB": "{:.3f}", "exito_pct": "{:.1f}",
                 "FEs_umbral_mediana": "{:,.0f}", "FEs_umbral_%presupuesto": "{:.1f}", "n": "{:d}"})

    for col, desv, nombre, ylabel, titulo in [
        ("tiempo_medio_s", "tiempo_desv_s", "fig3a_tiempo_vs_n", "Tiempo promedio por ejecución (s, escala log)",
         "Tiempo promedio frente al número de ciudades"),
        ("memoria_media_MB", "memoria_desv_MB", "fig3b_memoria_vs_n", "Memoria pico promedio (MB, escala log)",
         "Memoria máxima (tracemalloc) frente al número de ciudades")]:
        fig, ax = plt.subplots(figsize=(6.4, 4.2))
        for a in ALGS:
            d = efic[efic["algoritmo"] == a]
            ax.errorbar(d["n"], d[col], yerr=d[desv], color=COLORES[a], marker=MARCAS[a],
                        markersize=7, capsize=3, label=a)
        etiquetas_sin_choque(ax, [(a, NS[-1], efic[(efic.algoritmo == a) & (efic.n == NS[-1])][col].iloc[0])
                                  for a in ALGS])
        ax.set_yscale("log")
        ticks_legibles(ax)
        ax.set_xticks(NS)
        ax.set_xlabel("Número de ciudades n")
        ax.set_ylabel(ylabel)
        ax.set_title(titulo)
        ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.16))
        ax.set_xlim(NS[0] - 5, NS[-1] + 18)
        guardar(fig, FIG, nombre)

    # Escalabilidad de la calidad: mediana del error frente a n
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for a in ALGS:
        d = df[df["algoritmo"] == a].groupby("n")["error"]
        med, q1, q3 = d.median(), d.quantile(0.25), d.quantile(0.75)
        ax.plot(med.index, med.values, color=COLORES[a], marker=MARCAS[a], markersize=7, label=a)
        ax.fill_between(med.index, q1.values, q3.values, color=COLORES[a], alpha=0.12, linewidth=0)
    etiquetas_sin_choque(ax, [(a, NS[-1], df[(df.algoritmo == a) & (df.n == NS[-1])]["error"].median())
                              for a in ALGS])
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(bottom=0)
    ticks_legibles(ax)
    ax.set_xticks(NS)
    ax.set_xlim(NS[0] - 5, NS[-1] + 18)
    ax.set_xlabel("Número de ciudades n")
    ax.set_ylabel("Error relativo final (%, mediana y RIC)")
    ax.set_title("Calidad frente al tamaño del problema")
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    guardar(fig, FIG, "fig3d_error_vs_n")

    # =====================================================================
    # PUNTO 4a: curvas de convergencia en un eje común de FEs
    # =====================================================================
    corridas = [json.loads(l) for l in open(os.path.join(RES, "corridas.jsonl"))]
    fstar = df_todo.groupby(["n", "instancia"])["f_estrella"].first().to_dict()
    fracciones = np.geomspace(0.01, 1.0, 50)
    curvas = {}              # (alg, n) -> matriz corridas x puntos (error %)
    for c in corridas:
        B = c["presupuesto"]
        puntos = np.round(fracciones * B).astype(int)
        mejor = mejor_en_puntos(c["historial"], puntos)
        f0 = fstar[(c["n"], c["instancia"])]
        curvas.setdefault((c["algoritmo"], c["n"]), []).append(100 * (mejor - f0) / f0)
    curvas = {k: np.array(v) for k, v in curvas.items()}
    filas_curva = []
    for (a, n), M in curvas.items():
        for j, fr in enumerate(fracciones):
            col = M[:, j]
            filas_curva.append({"algoritmo": a, "n": n, "fraccion_presupuesto": fr,
                                "FEs": int(round(fr * cfg["presupuestos"][str(n)])),
                                "error_media": np.nanmean(col), "error_mediana": np.nanmedian(col),
                                "q25": np.nanpercentile(col, 25), "q75": np.nanpercentile(col, 75)})
    pd.DataFrame(filas_curva).to_csv(os.path.join(RES, "curvas_convergencia.csv"), index=False)

    fig, ejes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
    for ax, n in zip(ejes, NS):
        B = cfg["presupuestos"][str(n)]
        x = fracciones * B
        for a in ALGS:
            M = curvas[(a, n)]
            media = np.nanmean(M, axis=0)
            ax.plot(x, media, color=COLORES[a], label=a)
            ax.fill_between(x, np.nanpercentile(M, 25, axis=0), np.nanpercentile(M, 75, axis=0),
                            color=COLORES[a], alpha=0.15, linewidth=0)
        ax.axhline(eps_pct, color=TINTA2, linewidth=1, linestyle="--")
        ax.text(x[0], eps_pct * 1.15, "umbral 1%", color=TINTA2, fontsize=8)
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1)
        ax.set_ylim(bottom=0)
        ticks_legibles(ax)
        ax.set_title(f"n = {n}  (presupuesto {B:,} FEs)".replace(",", "."))
        ax.set_xlabel("Evaluaciones de la función objetivo (FEs, escala log)")
    ejes[0].set_ylabel("Error del mejor histórico (%)")
    ejes[1].legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    fig.suptitle("Curvas de convergencia promedio (línea = media; banda = percentiles 25–75)", y=1.02)
    guardar(fig, FIG, "fig4a_convergencia")

    # =====================================================================
    # PUNTO 4b: diagramas de caja del error relativo final
    # =====================================================================
    fig, ejes = plt.subplots(1, 3, figsize=(13, 4.3))
    for ax, n in zip(ejes, NS):
        datos = [df[(df["n"] == n) & (df["algoritmo"] == a)]["error"].values for a in ALGS]
        bp = ax.boxplot(datos, patch_artist=True, widths=0.6, showfliers=True,
                        medianprops={"color": TINTA, "linewidth": 1.5},
                        flierprops={"markersize": 3, "markeredgecolor": TINTA2})
        for caja, a in zip(bp["boxes"], ALGS):
            caja.set_facecolor(COLORES[a])
            caja.set_alpha(0.75)
            caja.set_edgecolor(TINTA2)
        ax.set_xticks(range(1, len(ALGS) + 1), ALGS)
        ax.set_yscale("symlog", linthresh=1)
        ax.set_ylim(bottom=0)
        ticks_legibles(ax)
        ax.axhline(eps_pct, color=TINTA2, linewidth=1, linestyle="--")
        ax.set_title(f"n = {n}  (R = {cfg['repeticiones']} × {len(cfg['semillas_publicas_instancias'])} instancias)")
        ax.set_ylabel("Error relativo final (%)")
    fig.suptitle("Distribución del error relativo final por algoritmo (línea discontinua = 1%)", y=1.02)
    guardar(fig, FIG, "fig4b_cajas_error")

    # =====================================================================
    # PUNTO 4d: rutas de los cinco métodos en la misma instancia
    # =====================================================================
    inst_ciud = pd.read_csv(os.path.join(RES, "instancias.csv"))
    n_ruta = 50 if 50 in NS else NS[-1]
    ciud = inst_ciud[(inst_ciud["n"] == n_ruta) & (inst_ciud["instancia"] == 0)][["x", "y"]].values
    fig, ejes = plt.subplots(1, len(ALGS), figsize=(3.1 * len(ALGS), 3.4))
    for ax, a in zip(ejes, ALGS):
        d = df[(df["n"] == n_ruta) & (df["instancia"] == 0) & (df["algoritmo"] == a)]
        fila = d.iloc[(d["costo"] - d["costo"].median()).abs().argsort().iloc[0]]   # corrida mediana
        ruta = np.array(list(map(int, fila["ruta"].split())))
        cerrada = np.append(ruta, ruta[0])
        ax.plot(ciud[cerrada, 0], ciud[cerrada, 1], color=COLORES[a], linewidth=1.5)
        ax.scatter(ciud[:, 0], ciud[:, 1], s=14, color=TINTA, zorder=3)
        ax.set_title(f"{a}: {fila['costo']:.1f} ({fila['error']:.1f}%)", fontsize=10)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal"); ax.grid(False)
        for lado in ax.spines.values():
            lado.set_visible(False)
    fig.suptitle(f"Ruta de la corrida MEDIANA de cada método (n = {n_ruta}, instancia 0)", y=1.03)
    guardar(fig, FIG, "fig4d_rutas")

    # =====================================================================
    # Análisis estadístico: Friedman + post hoc Wilcoxon con Holm
    # =====================================================================
    filas_f, filas_ph, filas_rank = [], [], []
    for n in NS:
        piv = (df[df["n"] == n].pivot_table(index=["instancia", "repeticion"], columns="algoritmo",
                                            values="costo")[ALGS])
        chi2, p = stats.friedmanchisquare(*[piv[a].values for a in ALGS])
        N, k = piv.shape
        W = chi2 / (N * (k - 1))                       # W de Kendall (tamaño del efecto)
        rangos = piv.rank(axis=1).mean()
        filas_f.append({"n": n, "bloques": N, "chi2": chi2, "p_valor": p, "W_Kendall": W})
        for a in ALGS:
            filas_rank.append({"n": n, "algoritmo": a, "rango_promedio": rangos[a]})
        pares = list(combinations(ALGS, 2))
        ps, efectos, meds = [], [], []
        for a, b in pares:
            dif = piv[a].values - piv[b].values
            res = stats.wilcoxon(piv[a].values, piv[b].values, zero_method="zsplit")
            ps.append(res.pvalue)
            # tamaño del efecto: correlación biserial de rangos emparejada
            r = stats.rankdata(np.abs(dif))
            efectos.append((r[dif > 0].sum() - r[dif < 0].sum()) / r.sum() if r.sum() > 0 else 0.0)
            meds.append(np.median(dif))
        for (a, b), p_raw, p_h, e, m in zip(pares, ps, holm(ps), efectos, meds):
            filas_ph.append({"n": n, "A": a, "B": b, "mediana(A-B)": m, "p_Wilcoxon": p_raw,
                             "p_Holm": p_h, "biserial_rangos": e,
                             "significativo": "sí" if p_h < 0.05 else "no",
                             "mejor": (a if e < 0 else b) if p_h < 0.05 else "empate"})
    pd.DataFrame(filas_f).to_csv(os.path.join(RES, "friedman.csv"), index=False)
    ph = pd.DataFrame(filas_ph)
    ph.to_csv(os.path.join(RES, "posthoc_wilcoxon_holm.csv"), index=False)
    rk = pd.DataFrame(filas_rank)
    rk.to_csv(os.path.join(RES, "rangos_promedio.csv"), index=False)
    tabla_latex(pd.DataFrame(filas_f), os.path.join(RES, "friedman.tex"),
                {"n": "{:d}", "bloques": "{:d}", "chi2": "{:.1f}", "p_valor": "{:.2e}", "W_Kendall": "{:.3f}"})
    tabla_latex(ph[["n", "A", "B", "mediana(A-B)", "p_Holm", "biserial_rangos", "mejor"]],
                os.path.join(RES, "posthoc.tex"),
                {"n": "{:d}", "mediana(A-B)": "{:.2f}", "p_Holm": "{:.1e}", "biserial_rangos": "{:.2f}"})

    # =====================================================================
    # PUNTO 4e: ranking por calidad, estabilidad y velocidad de convergencia
    # =====================================================================
    # Velocidad: área bajo la curva de error (en log-FEs) -> más pequeña = converge antes
    auc = {}
    for (a, n), M in curvas.items():
        if a in ALGS:
            auc[(a, n)] = np.nanmean(np.trapezoid(np.nan_to_num(M, nan=np.nanmax(M)),
                                                  np.log10(fracciones), axis=1))
    filas_rk = []
    for n in NS:
        base = pd.DataFrame({"algoritmo": ALGS})
        base["calidad (rango Friedman)"] = [rk[(rk.n == n) & (rk.algoritmo == a)]["rango_promedio"].iloc[0] for a in ALGS]
        base["estabilidad (desv. error %)"] = [estab.loc[(n, a)] for a in ALGS]
        base["velocidad (AUC error)"] = [auc[(a, n)] for a in ALGS]
        base["pos_calidad"] = base["calidad (rango Friedman)"].rank().astype(int)
        base["pos_estabilidad"] = base["estabilidad (desv. error %)"].rank().astype(int)
        base["pos_velocidad"] = base["velocidad (AUC error)"].rank().astype(int)
        base["pos_global"] = base[["pos_calidad", "pos_estabilidad", "pos_velocidad"]].mean(axis=1).rank(method="min").astype(int)
        base.insert(0, "n", n)
        filas_rk.append(base.sort_values("pos_global"))
    ranking = pd.concat(filas_rk)
    ranking.to_csv(os.path.join(RES, "ranking.csv"), index=False)
    tabla_latex(ranking[["n", "algoritmo", "pos_calidad", "pos_estabilidad", "pos_velocidad", "pos_global",
                         "calidad (rango Friedman)", "estabilidad (desv. error %)", "velocidad (AUC error)"]],
                os.path.join(RES, "ranking.tex"),
                {"n": "{:d}", "calidad (rango Friedman)": "{:.2f}",
                 "estabilidad (desv. error %)": "{:.2f}", "velocidad (AUC error)": "{:.1f}"})

    # =====================================================================
    # Pregunta opcional: híbrido ACO+2opt frente a sus componentes
    # =====================================================================
    if EXTRA:
        dfe = df_todo.copy()
        dfe["exito"] = dfe["error"] <= eps_pct + 1e-9
        filas_h = []
        for n in NS:
            piv = dfe[dfe["n"] == n].pivot_table(index=["instancia", "repeticion"], columns="algoritmo",
                                                  values="costo")
            for h in EXTRA:
                comps = ["ACO", "HC", "SA"]
                ps = []
                for c in comps:
                    ps.append(stats.wilcoxon(piv[h], piv[c], zero_method="zsplit").pvalue)
                for c, p_raw, p_h in zip(comps, ps, holm(ps)):
                    dif = piv[h].values - piv[c].values
                    filas_h.append({"n": n, "hibrido": h, "contra": c,
                                    "error_mediana_hibrido": dfe[(dfe.n == n) & (dfe.algoritmo == h)]["error"].median(),
                                    "error_mediana_contra": dfe[(dfe.n == n) & (dfe.algoritmo == c)]["error"].median(),
                                    "gana_hibrido_%": 100 * np.mean(dif < 0),
                                    "p_Holm": p_h})
        hib = pd.DataFrame(filas_h)
        hib.to_csv(os.path.join(RES, "hibrido.csv"), index=False)
        tabla_latex(hib[["n", "contra", "error_mediana_hibrido", "error_mediana_contra", "gana_hibrido_%", "p_Holm"]],
                    os.path.join(RES, "hibrido.tex"),
                    {"n": "{:d}", "error_mediana_hibrido": "{:.2f}", "error_mediana_contra": "{:.2f}",
                     "gana_hibrido_%": "{:.1f}", "p_Holm": "{:.1e}"})
        # Curvas: híbrido vs componentes
        fig, ejes = plt.subplots(1, 3, figsize=(13, 4.0), sharey=True)
        for ax, n in zip(ejes, NS):
            x = fracciones * cfg["presupuestos"][str(n)]
            for a in ["ACO", "HC", "SA"] + EXTRA:
                M = curvas[(a, n)]
                ax.plot(x, np.nanmean(M, axis=0), color=COLORES[a], label=a,
                        linewidth=2.6 if a in EXTRA else 1.6)
            ax.set_xscale("log"); ax.set_yscale("symlog", linthresh=1)
            ax.set_ylim(bottom=0); ticks_legibles(ax)
            ax.axhline(eps_pct, color=TINTA2, linewidth=1, linestyle="--")
            ax.set_title(f"n = {n}")
            ax.set_xlabel("FEs (escala log)")
        ejes[0].set_ylabel("Error medio del mejor histórico (%)")
        ejes[1].legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.2))
        fig.suptitle("Híbrido ACO + 2-opt frente a sus componentes (mismo presupuesto)", y=1.02)
        guardar(fig, FIG, "fig6_hibrido")

    print("Análisis terminado. Tablas en", RES, "y figuras en", FIG)


if __name__ == "__main__":
    main()
