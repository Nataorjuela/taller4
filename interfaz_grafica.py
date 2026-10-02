"""
INTERFAZ GRÁFICA DEL TALLER 4
=============================

Ejecutar:     python interfaz_grafica.py
Se abre sola en el navegador en  http://localhost:8765
(Para cerrarla: Ctrl + C en la terminal.)

Cómo funciona (arquitectura cliente-servidor, igual que una app web):
  * Este archivo es el SERVIDOR (backend). Solo usa la librería estándar de
    Python (http.server), así que no hay que instalar nada extra.
  * La página (frontend) está en  interfaz_web/  (HTML + CSS + JavaScript) y dibuja
    todas las gráficas dentro de la misma ventana.
  * Cuando se pulsa "Ejecutar", el navegador le pide al servidor que corra el
    algoritmo REAL de src/ con la interfaz común optimizar(...) y le devuelve
    el resultado en JSON.
  * Las pestañas de los puntos 2 a 5 leen los resultados oficiales del
    experimento (carpeta resultados/).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
from src import ALGORITMOS  # noqa: E402
from src.experimento import crear_instancia, semilla_ejecucion, semilla_instancia  # noqa: E402
from src.tsp import costo_ruta, es_ruta_valida, generar_ciudades, matriz_distancias  # noqa: E402

WEB = os.path.join(RAIZ, "interfaz_web")
RES = os.path.join(RAIZ, "resultados")
CFG = json.load(open(os.path.join(RAIZ, "configuracion.json"), encoding="utf-8"))
ALGS = CFG["algoritmos"]
EXTRA = CFG.get("algoritmos_extra", [])


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def limpio(obj):
    """Convierte tipos de NumPy/pandas a tipos JSON (NaN -> None)."""
    if isinstance(obj, dict):
        return {str(k): limpio(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [limpio(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return limpio(obj.tolist())
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def filas(df):
    return limpio(df.to_dict(orient="records"))


def reducir(puntos, maximo):
    """Toma como máximo 'maximo' elementos repartidos uniformemente (conserva el último)."""
    if len(puntos) <= maximo:
        return list(puntos)
    idx = np.unique(np.round(np.linspace(0, len(puntos) - 1, maximo)).astype(int))
    return [puntos[i] for i in idx]


# ---------------------------------------------------------------------------
# Resultados oficiales (se cargan una sola vez al iniciar)
# ---------------------------------------------------------------------------
def cargar_resultados():
    if not os.path.exists(os.path.join(RES, "ejecuciones.csv")):
        return {"disponible": False}
    leer = lambda n: pd.read_csv(os.path.join(RES, n))  # noqa: E731
    df = leer("ejecuciones.csv")
    out = {"disponible": True}

    out["eficiencia"] = filas(leer("tabla_eficiencia.csv"))
    out["rendimiento"] = filas(leer("tabla_rendimiento.csv"))
    out["rendimiento_instancia"] = filas(leer("tabla_rendimiento_por_instancia.csv"))
    out["ranking"] = filas(leer("ranking.csv"))
    out["friedman"] = filas(leer("friedman.csv"))
    out["rangos"] = filas(leer("rangos_promedio.csv"))
    out["posthoc"] = filas(leer("posthoc_wilcoxon_holm.csv"))
    if os.path.exists(os.path.join(RES, "hibrido.csv")):
        out["hibrido"] = filas(leer("hibrido.csv"))
    if os.path.exists(os.path.join(RES, "piloto_resumen.csv")):
        out["piloto"] = filas(leer("piloto_resumen.csv"))

    # Curvas de convergencia (media y banda 25-75) por algoritmo y tamaño
    cur = leer("curvas_convergencia.csv")
    out["curvas"] = {}
    for (a, n), g in cur.groupby(["algoritmo", "n"]):
        g = g.sort_values("FEs")
        out["curvas"].setdefault(str(int(n)), {})[a] = limpio({
            "FEs": g["FEs"].values, "media": g["error_media"].values, "mediana": g["error_mediana"].values,
            "q25": g["q25"].values, "q75": g["q75"].values})

    # Estadísticos de caja del error final
    df["exito"] = df["error"] <= 100 * CFG["epsilon"] + 1e-9
    out["cajas"] = {}
    for (n, a), g in df.groupby(["n", "algoritmo"]):
        e = g["error"].values
        q1, med, q3 = np.percentile(e, [25, 50, 75])
        ric = q3 - q1
        dentro = e[(e >= q1 - 1.5 * ric) & (e <= q3 + 1.5 * ric)]
        fuera = e[(e < q1 - 1.5 * ric) | (e > q3 + 1.5 * ric)]
        out["cajas"].setdefault(str(int(n)), {})[a] = limpio({
            "min": dentro.min(), "q1": q1, "mediana": med, "q3": q3, "max": dentro.max(),
            "atipicos": np.sort(fuera)[:60], "media": e.mean()})

    # Ruta de la corrida MEDIANA por (n, instancia, algoritmo)
    out["rutas_medianas"] = {}
    for (n, inst, a), g in df.groupby(["n", "instancia", "algoritmo"]):
        fila = g.iloc[(g["costo"] - g["costo"].median()).abs().argsort().iloc[0]]
        out["rutas_medianas"].setdefault(f"{int(n)}_{int(inst)}", {})[a] = limpio({
            "ruta": list(map(int, fila["ruta"].split())), "costo": fila["costo"], "error": fila["error"],
            "repeticion": fila["repeticion"]})

    # f* por instancia (referencia del error)
    out["f_estrella"] = {f"{int(n)}_{int(i)}": float(v)
                         for (n, i), v in df.groupby(["n", "instancia"])["f_estrella"].first().items()}
    out["total_corridas"] = int(len(df))
    return out


RESULTADOS = cargar_resultados()
F_ESTRELLA = RESULTADOS.get("f_estrella", {})
_DF_CACHE = {}


def tabla_ejecuciones():
    if "df" not in _DF_CACHE:
        _DF_CACHE["df"] = pd.read_csv(os.path.join(RES, "ejecuciones.csv"))
    return _DF_CACHE["df"]


# ---------------------------------------------------------------------------
# Instancias
# ---------------------------------------------------------------------------
def obtener_instancia(n, instancia, semilla_aleatoria=None):
    """Instancia oficial (n en 20/50/100 e instancia 0-4) o una aleatoria."""
    if semilla_aleatoria is None and n in CFG["tamanos"] and 0 <= instancia < len(CFG["semillas_publicas_instancias"]):
        sp = CFG["semillas_publicas_instancias"][instancia]
        ciudades, D = crear_instancia(n, sp)
        return ciudades, D, F_ESTRELLA.get(f"{n}_{instancia}"), f"oficial (semilla pública {sp})"
    semilla = int(semilla_aleatoria or 1)
    ciudades = generar_ciudades(n, semilla)
    return ciudades, matriz_distancias(ciudades), None, f"aleatoria (semilla {semilla})"


# ---------------------------------------------------------------------------
# Ejecución de un algoritmo (punto 1: interfaz común)
# ---------------------------------------------------------------------------
_CANDADO = threading.Lock()     # una ejecución a la vez: el tiempo medido es más limpio


def ejecutar_algoritmo(pet):
    alg = pet["algoritmo"]
    if alg not in ALGORITMOS:
        raise ValueError(f"Algoritmo desconocido: {alg}")
    n = int(pet.get("n", 50))
    if not 5 <= n <= 300:
        raise ValueError("n debe estar entre 5 y 300")
    instancia = int(pet.get("instancia", 0))
    aleatoria = pet.get("semilla_aleatoria")
    ciudades, D, f_est, desc = obtener_instancia(n, instancia, aleatoria if pet.get("usar_aleatoria") else None)
    presupuesto = int(pet.get("presupuesto") or CFG["presupuestos"].get(str(n), 20000))
    presupuesto = max(100, min(presupuesto, 300_000))
    semilla = int(pet.get("semilla", 7))
    parametros = {**CFG["parametros"].get(alg, {}), **(pet.get("parametros") or {})}

    with _CANDADO:
        # Pasada 1: sin tracemalloc (tiempo limpio) y guardando las rutas para la animación
        r = ALGORITMOS[alg](D, presupuesto, semilla, parametros, medir_memoria=False, guardar_rutas=True)
        memoria = None
        if pet.get("medir_memoria", True):
            # Pasada 2: misma semilla, con tracemalloc (memoria pico)
            r2 = ALGORITMOS[alg](D, presupuesto, semilla, parametros, medir_memoria=True)
            memoria = r2["memoria_mb"]

    ruta = r["mejor_ruta"]
    recalculado = costo_ruta(ruta, D)
    historial = [(int(a), float(b)) for a, b in r["historial"]]
    fotos = [(int(a), float(b), list(map(int, c))) for a, b, c in r["rutas_historial"]]
    ruta_inicial = fotos[0][2] if fotos else list(map(int, ruta))
    return limpio({
        "algoritmo": alg, "n": n, "instancia": instancia, "descripcion_instancia": desc,
        "semilla": semilla, "presupuesto": presupuesto, "parametros": parametros,
        "ciudades": ciudades.round(3), "mejor_ruta": ruta, "mejor_costo": r["mejor_costo"],
        "costo_inicial": historial[0][1] if historial else None, "ruta_inicial": ruta_inicial,
        "f_estrella": f_est,
        "error_pct": None if not f_est else 100 * (r["mejor_costo"] - f_est) / f_est,
        "evaluaciones": r["evaluaciones"], "fe_mejor": r["fe_mejor"],
        "tiempo_s": r["tiempo_s"], "memoria_mb": memoria,
        "historial": reducir(historial, 600),
        "fotos": reducir(fotos, 120),
        "mejoras": len(historial),
        "verificaciones": {
            "ruta_valida": bool(es_ruta_valida(ruta, n)),
            "costo_coincide": bool(abs(recalculado - r["mejor_costo"]) < 1e-6),
            "presupuesto_exacto": bool(r["evaluaciones"] == presupuesto),
            "historial_no_empeora": all(a[1] >= b[1] for a, b in zip(historial, historial[1:])),
        },
    })


def vista_csv(q):
    df = tabla_ejecuciones()
    for col in ("algoritmo", "n", "instancia"):
        v = q.get(col, [""])[0]
        if v not in ("", "todos"):
            df = df[df[col].astype(str) == v]
    cols = ["algoritmo", "n", "instancia", "repeticion", "semilla", "costo", "error", "tiempo",
            "memoria", "FEs_mejor", "FEs_umbral", "mejora"]
    return {"total": int(len(df)), "filas": filas(df[cols].head(150))}


def tabla_semillas():
    salida = []
    for n in CFG["tamanos"]:
        for inst, sp in enumerate(CFG["semillas_publicas_instancias"]):
            salida.append({"n": n, "instancia": inst, "semilla_publica": sp,
                           "semilla_instancia": semilla_instancia(n, sp),
                           "semillas_rep_0_a_2": [semilla_ejecucion(CFG["semilla_maestra"], n, inst, r) for r in range(3)]})
    return salida


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------
class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=WEB, **k)

    def log_message(self, fmt, *args):      # consola limpia
        texto = fmt % args if args else fmt
        if "/api/ejecutar" in texto:
            sys.stdout.write(time.strftime("[%H:%M:%S] ") + texto + "\n")

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _archivo(self, ruta, tipo):
        if not os.path.exists(ruta):
            return self._json({"error": "no existe"}, 404)
        datos = open(ruta, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/api/config":
                return self._json(limpio({"config": CFG, "algoritmos": ALGS, "extra": EXTRA,
                                          "semillas": tabla_semillas(),
                                          "resultados_disponibles": RESULTADOS.get("disponible", False),
                                          "total_corridas": RESULTADOS.get("total_corridas", 0)}))
            if u.path == "/api/resultados":
                return self._json(RESULTADOS)
            if u.path == "/api/instancia":
                n, inst = int(q.get("n", ["50"])[0]), int(q.get("instancia", ["0"])[0])
                ciudades, _, f_est, desc = obtener_instancia(n, inst)
                return self._json(limpio({"ciudades": ciudades.round(3), "f_estrella": f_est, "descripcion": desc}))
            if u.path == "/api/csv":
                return self._json(vista_csv(q))
            if u.path == "/favicon.ico":
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            if u.path == "/descargas/ejecuciones.csv":
                return self._archivo(os.path.join(RES, "ejecuciones.csv"), "text/csv; charset=utf-8")
            if u.path == "/descargas/informe.pdf":
                return self._archivo(os.path.join(RAIZ, "informe", "informe.pdf"), "application/pdf")
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 400)
        return super().do_GET()

    def do_POST(self):
        u = urlparse(self.path)
        if u.path != "/api/ejecutar":
            return self._json({"error": "ruta desconocida"}, 404)
        try:
            largo = int(self.headers.get("Content-Length", 0))
            pet = json.loads(self.rfile.read(largo) or b"{}")
            return self._json(ejecutar_algoritmo(pet))
        except Exception as e:  # noqa: BLE001
            return self._json({"error": str(e)}, 400)


def main():
    ap = argparse.ArgumentParser(description="Interfaz gráfica del Taller 4")
    ap.add_argument("--puerto", type=int, default=8765)
    ap.add_argument("--no-abrir", action="store_true", help="no abrir el navegador automáticamente")
    args = ap.parse_args()
    servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    url = f"http://localhost:{args.puerto}"
    print("=" * 64)
    print("  Interfaz gráfica del Taller 4 - Metaheurísticas en el TSP")
    print(f"  Abierta en: {url}")
    if not RESULTADOS.get("disponible"):
        print("  (Aviso: no hay resultados en resultados/. Las pestañas 2-5 estarán vacías;")
        print("   ejecute ejecutar_experimentos.py y experimentos/analizar_resultados.py)")
    print("  Para cerrarla presione Ctrl + C")
    print("=" * 64)
    if not args.no_abrir:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nInterfaz cerrada.")


if __name__ == "__main__":
    main()
