"""
Fase piloto (permitida por el protocolo): se prueban pocas configuraciones de
parámetros en instancias DISTINTAS a las del experimento final (semillas
901-903) para elegir los parámetros ANTES del experimento. Así no se hace
"trampa" ajustando los parámetros a las instancias con las que se reporta.

Uso:  python experimentos/piloto.py
"""
import itertools
import json
import os
import sys
from multiprocessing import Pool

import pandas as pd

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)
from src.experimento import correr, semilla_ejecucion  # noqa: E402

N, PRESUPUESTO, INSTANCIAS, REPS = 50, 30000, [901, 902, 903], 5

REJILLA = {
    "GA":  {"poblacion": [50, 100], "prob_mutacion": [0.1, 0.3, 0.6]},
    "ACO": {"beta": [2.0, 3.0, 5.0], "rho": [0.1, 0.3]},
    "PSO": {"particulas": [30, 50], "vmax": [0.1, 0.5]},
    "HC":  {"paciencia_factor": [0.5, 1.0, 2.0]},
    "SA":  {"p0": [0.2, 0.5, 0.8], "ratio_final": [1e-2, 1e-3, 1e-4]},
}


def tareas():
    for alg, rej in REJILLA.items():
        claves = list(rej)
        for valores in itertools.product(*rej.values()):
            params = dict(zip(claves, valores))
            for inst in INSTANCIAS:
                for rep in range(REPS):
                    yield {"algoritmo": alg, "n": N, "instancia": inst, "semilla_publica": inst,
                           "repeticion": rep, "semilla": semilla_ejecucion(7, N, inst, rep),
                           "presupuesto": PRESUPUESTO, "parametros": params,
                           "medir_memoria": False, "_config": json.dumps(params)}


def _correr(t):
    fila = correr(t)
    fila["config"] = t["_config"]
    fila.pop("historial"); fila.pop("ruta")
    return fila


if __name__ == "__main__":
    with Pool(2) as pool:
        filas = pool.map(_correr, list(tareas()), chunksize=4)
    df = pd.DataFrame(filas)
    # Error relativo a la mejor ruta encontrada en el piloto para cada instancia
    df["f_ref"] = df.groupby("instancia")["costo"].transform("min")
    df["error_%"] = 100 * (df["costo"] - df["f_ref"]) / df["f_ref"]
    resumen = (df.groupby(["algoritmo", "config"])["error_%"]
                 .agg(["mean", "median", "std"]).round(2).reset_index()
                 .sort_values(["algoritmo", "mean"]))
    os.makedirs(os.path.join(RAIZ, "resultados"), exist_ok=True)
    resumen.to_csv(os.path.join(RAIZ, "resultados", "piloto_resumen.csv"), index=False)
    print(resumen.to_string(index=False))
