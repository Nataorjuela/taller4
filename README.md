# Taller 4 – Comparación de metaheurísticas en el TSP

Comparación reproducible de cinco métodos de optimización sobre el problema del viajante (TSP):
algoritmo genético (GA), colonia de hormigas (ACO), enjambre de partículas (PSO), ascenso de colinas (HC)
y temple simulado (SA), con el mismo presupuesto de evaluaciones de la función objetivo (FEs).
Incluye el híbrido opcional **ACO + 2-opt** y una **interfaz gráfica** para explorar todo.

---

## Inicio rápido (Windows + VS Code)

1. Descomprima el zip y abra en VS Code la carpeta **`taller4`** (Archivo → Abrir carpeta…).
   Debe ser la carpeta que contiene este README.
2. Abra una terminal (`Ctrl + ñ`) y ejecute:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   Si Windows dice que la ejecución de scripts está deshabilitada, ejecute una sola vez
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelva a activar el entorno.
   Si `python` no se reconoce, use `py` en su lugar.
   Si la instalación falla por alguna versión (por ejemplo con Python 3.14), instale sin fijar versiones:
   `python -m pip install numpy pandas matplotlib scipy`
3. En VS Code: `Ctrl + Shift + P` → **Python: Select Interpreter** → elija el que dice `.venv`.
4. Abra la interfaz gráfica:

   ```powershell
   python interfaz_grafica.py
   ```

   Se abre sola en el navegador en **http://localhost:8765**.
   Si no se abre, copie esa dirección en Chrome o Edge. Para cerrarla: `Ctrl + C` en la terminal.

   Otra forma: panel **Ejecutar y depurar** (`Ctrl + Shift + D`) → elija
   **★ INTERFAZ GRÁFICA (abre el navegador)** → ▶.

No hace falta volver a correr el experimento: los resultados oficiales (2 700 corridas) ya vienen en `resultados/`.

---

## La interfaz gráfica

Todo se ve en una sola ventana, organizada en pestañas que siguen los puntos del taller.

| Pestaña | Qué puede hacer |
|---|---|
| **1 · Ejecutar algoritmos** | Elegir el tamaño (20, 50, 100 u otro), la instancia, la semilla y el presupuesto. Luego elegir un algoritmo (GA, ACO, PSO, HC, SA o el híbrido), cambiar sus parámetros y pulsar **▶ Ejecutar**. Muestra el mejor costo, el error, la mejora, el tiempo, la memoria, la **ruta animada** (botón ▶ o barra deslizante), la **curva de convergencia**, las verificaciones del punto 1 y el diccionario que devuelve `optimizar()`. El botón **⚖ Comparar los 5** ejecuta todos sobre la misma instancia y los compara. |
| **2 · Diseño experimental** | Por qué se cuentan evaluaciones y no iteraciones, el protocolo, las semillas, la fase piloto y un explorador del CSV con filtros y descarga. |
| **3 · Eficiencia** | Tiempo, memoria, costo por cada 1000 evaluaciones y error frente a n. Incluye la tabla de éxito y de FEs necesarias para llegar al 1 %, y quién escala mejor. |
| **4 · Rendimiento** | Curvas de convergencia con banda, diagramas de caja, tabla de rendimiento, costos por instancia, rutas de la corrida mediana de cada método y ranking. |
| **5 · Conclusiones** | Friedman, puesto promedio, matriz de Wilcoxon + Holm ("quién le gana a quién") y las 7 preguntas respondidas con los números. |
| **Híbrido (opcional)** | ACO + 2-opt frente a ACO, HC y SA, con prueba estadística. |
| **Teoría rápida** | Resumen del TSP, qué es una metaheurística y los cinco algoritmos. Enlaces a la guía y al informe en PDF. |

En las gráficas:

- Pase el mouse por encima para ver los valores.
- Use los botones de colores para mostrar u ocultar algoritmos.
- Use los selectores para cambiar el tamaño n.

**Cómo está hecha.** `interfaz_grafica.py` es un pequeño servidor que usa solo la librería estándar de Python
(no requiere instalar nada extra). La página está en `interfaz_web/` (HTML, CSS y JavaScript, sin internet) y
dibuja las gráficas dentro de la misma ventana. Al pulsar *Ejecutar*, el servidor corre el algoritmo **real**
de `src/` con la interfaz común `optimizar(distancias, presupuesto, semilla, parametros)`.

Opciones: `python interfaz_grafica.py --puerto 9000` (otro puerto) · `--no-abrir` (no abrir el navegador).

---

## Ejecutar el experimento desde la terminal

```powershell
python pruebas/test_algoritmos.py                                  # 1) pruebas (≈ 5 s)
python experimentos/piloto.py                                      # 2) fase piloto (opcional, ≈ 3 min)
python ejecutar_experimentos.py --config configuracion.json        # 3) experimento completo (30-40 min)
python experimentos/analizar_resultados.py --config configuracion.json   # 4) tablas y figuras
```

- Versión rápida (≈ 10 s, en `resultados_demo/`): `python ejecutar_experimentos.py --config configuracion_rapida.json`
- Cada corrida se guarda apenas termina en `resultados/corridas.jsonl`. Si el proceso se interrumpe, al relanzarlo continúa donde iba.
- Todos los parámetros están en `configuracion.json`: para repetir con otros valores se cambia ese archivo, no el código.

**Importante:** los archivos de `src/` son módulos (piezas) y no se ejecutan solos. Si le da ▶ a `src/interfaz.py`,
aparece el error *"attempted relative import with no known parent package"*. Ejecute siempre los archivos de la raíz,
de `demos/`, de `experimentos/` o de `pruebas/`.

## Scripts de consola por punto (alternativa a la interfaz)

En **Ejecutar y depurar** (`Ctrl + Shift + D`) también aparecen *Punto 1 … Punto 5*, *Opcional*, *Pruebas*, etc.

| Script | Qué muestra |
|---|---|
| `demos/punto1_interfaz.py` | los 5 algoritmos con la misma llamada, el diccionario de salida, verificaciones, rutas y curvas |
| `demos/punto2_experimento.py` | configuración, semillas y un experimento rápido en `resultados_demo/` |
| `demos/punto3_eficiencia.py` | tiempo, memoria, éxito, FEs al 1 % y gráficas frente a n |
| `demos/punto4_rendimiento.py` | tabla de rendimiento, ranking, convergencia, cajas y rutas |
| `demos/punto5_conclusiones.py` | Friedman, Wilcoxon + Holm y la evidencia de cada pregunta |
| `demos/opcional_hibrido.py` | comparación del híbrido ACO + 2-opt |

---

## Semillas (reproducibilidad)

- **Instancias:** semillas públicas **101, 102, 103, 104, 105**. La semilla real de cada instancia es `SeedSequence([semilla_publica, n])`.
- **Corridas:** `SeedSequence([2026, n, instancia, repeticion])`, **la misma para todos los algoritmos** (comparaciones emparejadas).
- **Fase piloto:** instancias 901, 902 y 903, distintas de las del experimento final.

## Estructura

```
interfaz_grafica.py        INTERFAZ GRÁFICA (servidor local) -> python interfaz_grafica.py
interfaz_web/              página de la interfaz (index.html, estilos.css, graficas.js, app.js, textos.js)
src/                       implementación modular
  tsp.py                   instancias, distancias, función objetivo, Evaluador (conteo de FEs)
  vecindad.py              vecino 2-opt compartido por HC y SA
  interfaz.py              interfaz común (envoltorio): semilla, tiempo, memoria, verificación
  genetico.py              GA: torneo, cruce OX, mutación por inversión, elitismo
  colonia_hormigas.py      ACO: Ant System elitista
  enjambre_particulas.py   PSO con claves aleatorias
  ascenso_colinas.py       HC con reinicios
  temple_simulado.py       SA con criterio de Metropolis y enfriamiento geométrico
  hibrido_aco_2opt.py      híbrido opcional
  experimento.py           semillas y ejecución de una corrida
experimentos/              piloto.py, analizar_resultados.py, tablas_guia.py
demos/                     un script de consola por punto
pruebas/test_algoritmos.py pruebas automáticas
ejecutar_experimentos.py   comando principal del experimento
configuracion.json         todos los parámetros del experimento
configuracion_rapida.json  versión corta para probar
resultados/                CSV originales y tablas resumidas (.csv y .tex)
figuras/                   gráficas (.png y .pdf)
informe/                   informe.tex / informe.pdf (6 páginas)
guia/                      guía explicada (.tex y .pdf)
.vscode/launch.json        menú de ejecución de VS Code
```

## Archivos de resultados principales

| Archivo | Contenido |
|---|---|
| `resultados/ejecuciones.csv` | una fila por corrida: algoritmo, n, instancia, repeticion, semilla, costo, error, tiempo, memoria, FEs_mejor, … |
| `resultados/corridas.jsonl` | lo mismo + historial completo (FEs, mejor costo) |
| `resultados/tabla_rendimiento.csv` | mejor, media, mediana, desviación, error, RIC, tasa de éxito |
| `resultados/tabla_eficiencia.csv` | tiempo, memoria, FEs para alcanzar error ≤ 1 % |
| `resultados/friedman.csv`, `posthoc_wilcoxon_holm.csv`, `rangos_promedio.csv` | estadística |
| `resultados/ranking.csv` | ranking por calidad, estabilidad y velocidad |
| `resultados/hibrido.csv` | comparación del híbrido con sus componentes |

## Notas de medición

- **Tiempo:** se mide con `time.perf_counter` sin `tracemalloc`, porque `tracemalloc` hace el código 2–4 veces más lento.
- **Memoria pico:** se mide con `tracemalloc` en una segunda pasada con la misma semilla, para las repeticiones 0–4 de cada instancia.
- **`f*` (referencia del error):** es la mejor ruta encontrada por cualquier algoritmo en todas las corridas de esa instancia.

## Guía explicada e informe

- `guia/guia_taller4.tex` es un solo archivo LaTeX autocontenido; solo necesita la carpeta `figuras/`. `guia/guia_taller4.pdf` es su versión compilada.
- `informe/informe.tex` y `informe/informe.pdf` son el informe de entrega.

Ambos compilan con pdfLaTeX o XeLaTeX. En VS Code, con la extensión LaTeX Workshop, basta con guardar.

Probado con Python 3.11 (NumPy 2.4, pandas 3.0, SciPy 1.17, Matplotlib 3.10) y Chrome/Edge.
