"""
PUNTO 2 - Diseño experimental y reproducibilidad.
Muestra la configuración centralizada, las semillas y ejecuta una versión
RÁPIDA del experimento (configuracion_rapida.json, ~1 minuto) en la carpeta
resultados_demo/, para ver cómo se construyen las instancias y el CSV.
Los resultados OFICIALES (2700 corridas) ya están en resultados/.
"""
import json
import subprocess
import sys

import _comun
from _comun import pd, titulo

from src.experimento import semilla_ejecucion, semilla_instancia

cfg = json.load(open("configuracion.json", encoding="utf-8"))
titulo("PUNTO 2 - Configuración centralizada (configuracion.json)")
for clave in ["tamanos", "presupuestos", "semillas_publicas_instancias", "repeticiones", "algoritmos"]:
    print(f"  {clave:<30} {cfg[clave]}")
print("  parámetros:")
for alg, p in cfg["parametros"].items():
    print(f"    {alg:<9} {p}")

titulo("Semillas: la MISMA para todos los algoritmos (comparación emparejada)")
for rep in range(3):
    print(f"  n=50, instancia 0, repetición {rep}:  semilla = {semilla_ejecucion(2026, 50, 0, rep)}"
          f"   (GA, ACO, PSO, HC y SA usan esta)")
print(f"  Semilla real de la instancia pública 101 con n=50: {semilla_instancia(50, 101)}")

titulo("Ejecutando la versión rápida del experimento (configuracion_rapida.json)")
subprocess.run([sys.executable, "ejecutar_experimentos.py", "--config", "configuracion_rapida.json"], check=True)

df = pd.read_csv("resultados_demo/ejecuciones.csv")
titulo("Primeras filas del CSV (columnas pedidas por el taller)")
cols = ["algoritmo", "n", "instancia", "repeticion", "semilla", "costo", "error", "tiempo", "memoria", "FEs_mejor"]
print(df[cols].head(12).to_string(index=False))
print(f"\nTotal de filas: {len(df)}  ->  guardado en resultados_demo/ejecuciones.csv")
print("Archivo oficial con las 2700 corridas: resultados/ejecuciones.csv")
