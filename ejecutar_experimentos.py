"""
Comando principal del taller:

    python ejecutar_experimentos.py --config configuracion.json

1) Genera las instancias con las semillas públicas del archivo de configuración.
2) Ejecuta TODAS las combinaciones algoritmo x tamaño x instancia x repetición
   con el mismo presupuesto de FEs y las mismas semillas para todos.
3) Guarda cada corrida apenas termina (resultados/corridas.jsonl), de modo que
   si el proceso se interrumpe se puede relanzar y continúa donde iba.
4) Al final calcula f* por instancia y escribe resultados/ejecuciones.csv con
   las columnas pedidas (algoritmo, n, instancia, repeticion, semilla, costo,
   error, tiempo, memoria, FEs_mejor) + mejor costo en los puntos de control.

Después ejecute:  python experimentos/analizar_resultados.py --config configuracion.json
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
from src.experimento import correr, crear_instancia, semilla_ejecucion  # noqa: E402
from src.tsp import mejor_en_puntos  # noqa: E402


def construir_tareas(cfg, hechas):
    algs = cfg["algoritmos"] + cfg.get("algoritmos_extra", [])
    tareas = []
    for n in sorted(cfg["tamanos"], reverse=True):          # las más pesadas primero
        for inst, sp in enumerate(cfg["semillas_publicas_instancias"]):
            for rep in range(cfg["repeticiones"]):
                semilla = semilla_ejecucion(cfg["semilla_maestra"], n, inst, rep)
                for alg in algs:
                    clave = (alg, n, inst, rep)
                    if clave in hechas:
                        continue
                    tareas.append({
                        "algoritmo": alg, "n": n, "instancia": inst, "semilla_publica": sp,
                        "repeticion": rep, "semilla": semilla,
                        "presupuesto": cfg["presupuestos"][str(n)],
                        "parametros": cfg["parametros"][alg],
                        "medir_memoria": rep < cfg["repeticiones_con_memoria"],
                    })
    return tareas


def guardar_instancias(cfg, carpeta):
    filas = []
    for n in cfg["tamanos"]:
        for inst, sp in enumerate(cfg["semillas_publicas_instancias"]):
            ciudades, _ = crear_instancia(n, sp)
            for c, (x, y) in enumerate(ciudades):
                filas.append({"n": n, "instancia": inst, "semilla_publica": sp, "ciudad": c, "x": x, "y": y})
    pd.DataFrame(filas).to_csv(os.path.join(carpeta, "instancias.csv"), index=False)


def consolidar(cfg, carpeta):
    corridas = [json.loads(l) for l in open(os.path.join(carpeta, "corridas.jsonl"))]
    df = pd.DataFrame([{k: v for k, v in c.items() if k != "historial"} for c in corridas])
    # f*: mejor valor encontrado por CUALQUIER algoritmo en TODAS las corridas
    df["f_estrella"] = df.groupby(["n", "instancia"])["costo"].transform("min")
    df["error"] = 100 * (df["costo"] - df["f_estrella"]) / df["f_estrella"]
    df["tiempo_por_1000FEs"] = 1000 * df["tiempo"] / df["evaluaciones"]
    # Mejora(%) = 100 (f_inicial - f_r) / f_inicial, con f_inicial = costo de la primera ruta evaluada
    df["f_inicial"] = [c["historial"][0][1] for c in corridas]
    df["mejora"] = 100 * (df["f_inicial"] - df["costo"]) / df["f_inicial"]
    # Mejor costo en los puntos de control (1%, 5%, ..., 100% del presupuesto)
    fr = cfg["fracciones_control"]
    control = []
    umbral_fes = []
    for c, fstar in zip(corridas, df["f_estrella"]):
        puntos = np.round(np.array(fr) * c["presupuesto"]).astype(int)
        control.append(mejor_en_puntos(c["historial"], puntos))
        # FEs necesarias para llegar a error <= epsilon (NaN si nunca llegó)
        meta = fstar * (1 + cfg["epsilon"])
        fe = next((fe for fe, v in c["historial"] if v <= meta + 1e-9), np.nan)
        umbral_fes.append(fe)
    control = np.array(control)
    for k, f in enumerate(fr):
        df[f"mejor_{int(round(f * 100))}pct"] = control[:, k]
    df["FEs_umbral"] = umbral_fes
    columnas = ["algoritmo", "n", "instancia", "repeticion", "semilla", "costo", "error",
                "tiempo", "memoria", "FEs_mejor", "evaluaciones", "presupuesto", "f_estrella",
                "tiempo_por_1000FEs", "FEs_umbral", "f_inicial", "mejora"] + [f"mejor_{int(round(f * 100))}pct" for f in fr] + ["ruta"]
    df = df[columnas].sort_values(["n", "instancia", "algoritmo", "repeticion"])
    df.to_csv(os.path.join(carpeta, "ejecuciones.csv"), index=False)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configuracion.json")
    ap.add_argument("--solo-consolidar", action="store_true")
    args = ap.parse_args()
    cfg = json.load(open(args.config, encoding="utf-8"))
    carpeta = os.path.join(RAIZ, cfg["carpeta_resultados"])
    os.makedirs(carpeta, exist_ok=True)
    guardar_instancias(cfg, carpeta)

    archivo = os.path.join(carpeta, "corridas.jsonl")
    hechas = set()
    if os.path.exists(archivo):
        for l in open(archivo):
            c = json.loads(l)
            hechas.add((c["algoritmo"], c["n"], c["instancia"], c["repeticion"]))

    if not args.solo_consolidar:
        tareas = construir_tareas(cfg, hechas)
        print(f"Corridas pendientes: {len(tareas)} (ya hechas: {len(hechas)})", flush=True)
        t0 = time.time()
        with Pool(cfg["procesos"]) as pool, open(archivo, "a") as salida:
            for k, fila in enumerate(pool.imap_unordered(correr, tareas, chunksize=1), 1):
                salida.write(json.dumps(fila) + "\n")
                salida.flush()
                if k % 100 == 0 or k == len(tareas):
                    print(f"  {k}/{len(tareas)}  ({time.time() - t0:.0f} s)", flush=True)

    df = consolidar(cfg, carpeta)
    print("Listo:", len(df), "filas en", os.path.join(cfg["carpeta_resultados"], "ejecuciones.csv"))


if __name__ == "__main__":
    main()
