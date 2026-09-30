"""Utilidades compartidas por los scripts de demostración (no se ejecuta solo)."""
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.chdir(RAIZ)                      # así funciona igual con el botón ▶ de VS Code

import matplotlib.pyplot as plt     # noqa: E402
import pandas as pd                 # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda x: f"{x:,.3f}")

COLORES = {"GA": "#2a78d6", "ACO": "#eb6834", "PSO": "#1baf7a", "HC": "#eda100",
           "SA": "#e87ba4", "ACO+2opt": "#008300"}


def titulo(texto):
    print("\n" + "=" * 78)
    print(" " + texto)
    print("=" * 78)


def leer(nombre):
    ruta = os.path.join(RAIZ, "resultados", nombre)
    if not os.path.exists(ruta):
        sys.exit(f"No encuentro {ruta}. Ejecute primero: python ejecutar_experimentos.py "
                 f"y python experimentos/analizar_resultados.py")
    return pd.read_csv(ruta)


def mostrar_figuras(nombres, titulo_ventana):
    """Abre las figuras PNG ya generadas (una ventana por figura)."""
    for n in nombres:
        ruta = os.path.join(RAIZ, "figuras", n + ".png")
        if not os.path.exists(ruta):
            print("  (falta la figura", ruta, ")")
            continue
        img = plt.imread(ruta)
        alto, ancho = img.shape[:2]
        fig = plt.figure(figsize=(min(16, ancho / 130), min(9, alto / 130)))
        fig.canvas.manager.set_window_title(f"{titulo_ventana} - {n}")
        plt.imshow(img)
        plt.axis("off")
        plt.tight_layout()
    print("\nCierre las ventanas de las gráficas para terminar.")
    plt.show()
