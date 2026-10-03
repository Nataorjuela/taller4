# Taller 4 – Comparación de metaheurísticas en el TSP

Comparación reproducible de cinco métodos de optimización sobre el problema del viajante (TSP):
algoritmo genético (GA), colonia de hormigas (ACO), enjambre de partículas (PSO), ascenso de colinas (HC)
y temple simulado (SA), con el mismo presupuesto de evaluaciones de la función objetivo (FEs).
Incluye el híbrido opcional **ACO + 2-opt** y una **interfaz gráfica** para explorar todo.

**Estudiantes:** Jimmy Millán, Santiago León y Natalia Orjuela.

---

## Ejecutar en un PC local (Windows + VS Code)

1. Instale Python 3.11 y Git. Clone el repositorio y entre a la carpeta del proyecto desde PowerShell:

   ```powershell
   git clone https://github.com/Nataorjuela/taller4.git
   cd taller4
   ```

   Si descargó el proyecto como ZIP, descomprímalo y abra en VS Code la carpeta `taller4`
   (la carpeta que contiene este README); en ese caso, omita `git clone`.
2. Cree el entorno virtual e instale las dependencias:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   Si `python` no se reconoce, cree el entorno con
   `py -3.11 -m venv .venv` y use `.\.venv\Scripts\python.exe` para los comandos siguientes.
3. Compruebe la instalación:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q pruebas/test_algoritmos.py
   ```

4. Inicie la interfaz gráfica local:

   ```powershell
   .\.venv\Scripts\python.exe interfaz_grafica.py
   ```

   Abra **http://localhost:8765** en Chrome o Edge si no se abre automáticamente. Detenga el
   servidor con `Ctrl + C`. Para usar otro puerto, agregue `--puerto 9000`.

No hace falta volver a correr el experimento: los resultados oficiales (2 700 corridas) ya vienen en `resultados/`.

## Ejecutar en Google Colab

Colab sirve para instalar las dependencias, ejecutar las pruebas y volver a generar los experimentos
y sus análisis. La interfaz web está pensada para ejecutarse en un PC local; el servidor escucha en
`127.0.0.1`, por lo que `localhost` de Colab no es el navegador de tu PC. Para explorar la interfaz,
sigue los pasos de la sección anterior.

En un cuaderno nuevo de Colab, ejecuta estas instrucciones en celdas separadas y en orden:

1. Clona el repositorio y cambia al directorio del proyecto:

   ```python
   !git clone https://github.com/Nataorjuela/taller4.git
   %cd /content/taller4
   ```

2. Instala las dependencias declaradas por el proyecto:

   ```python
   !python -m pip install -r requirements.txt
   ```

3. Ejecuta las pruebas:

   ```python
   !python -m pytest -q pruebas/test_algoritmos.py
   ```

4. (Opcional) Ejecuta una prueba experimental rápida y genera sus tablas y figuras:

   ```python
   !python ejecutar_experimentos.py --config configuracion_rapida.json
   !python experimentos/analizar_resultados.py --config configuracion_rapida.json
   ```

5. Para repetir el experimento completo en vez del rápido, ejecuta estos comandos en su lugar.
   Puede tardar entre 30 y 40 minutos; Colab puede interrumpir sesiones largas:

   ```python
   !python ejecutar_experimentos.py --config configuracion.json
   !python experimentos/analizar_resultados.py --config configuracion.json
   ```

Los archivos de Colab se pierden al eliminar el entorno de ejecución. Si necesitas conservar los
resultados generados, monta Google Drive antes del paso 4 o 5 y copia allí las carpetas al terminar:

```python
from google.colab import drive
drive.mount("/content/drive")
```

```python
!mkdir -p /content/drive/MyDrive/taller4
!cp -r resultados figuras /content/drive/MyDrive/taller4/
```

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
| **Teoría rápida** | Resumen del TSP, qué es una metaheurística y los cinco algoritmos. Incluye enlace al informe final en PDF. |

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
.\.venv\Scripts\python.exe -m pytest -q pruebas/test_algoritmos.py   # 1) pruebas
.\.venv\Scripts\python.exe experimentos/piloto.py                    # 2) piloto (opcional)
.\.venv\Scripts\python.exe ejecutar_experimentos.py --config configuracion.json
.\.venv\Scripts\python.exe experimentos/analizar_resultados.py --config configuracion.json
```

- Cada corrida se guarda apenas termina en `resultados/corridas.jsonl`. Si el proceso se interrumpe, al relanzarlo continúa donde iba.
- Todos los parámetros están en `configuracion.json`: para repetir con otros valores se cambia ese archivo, no el código.
- Para una ejecución de prueba más corta, reemplaza `configuracion.json` por `configuracion_rapida.json` en los dos últimos comandos.

**Importante:** los archivos de `src/` son módulos (piezas) y no se ejecutan solos. Si le da ▶ a `src/interfaz.py`,
aparece el error *"attempted relative import with no known parent package"*. Ejecute siempre los archivos de la raíz,
de `demos/`, de `experimentos/` o de `pruebas/`.

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
experimentos/              piloto.py, analizar_resultados.py
pruebas/test_algoritmos.py pruebas automáticas
ejecutar_experimentos.py   comando principal del experimento
configuracion.json         todos los parámetros del experimento
resultados/                CSV originales y tablas resumidas
figuras/                   gráficas usadas por el informe (.png)
informe/                   informe.tex / informe.pdf (6 páginas)
.vscode/launch.json        menú de ejecución de VS Code
```

## Archivos de resultados principales

| Archivo | Contenido |
|---|---|
| `resultados/ejecuciones.csv` | una fila por corrida: algoritmo, n, instancia, repeticion, semilla, costo, error, tiempo, memoria, FEs_mejor, … |
| `resultados/tabla_rendimiento.csv` | mejor, media, mediana, desviación, error, RIC, tasa de éxito |
| `resultados/tabla_eficiencia.csv` | tiempo, memoria, FEs para alcanzar error ≤ 1 % |
| `resultados/friedman.csv`, `posthoc_wilcoxon_holm.csv`, `rangos_promedio.csv` | estadística |
| `resultados/ranking.csv` | ranking por calidad, estabilidad y velocidad |
| `resultados/hibrido.csv` | comparación del híbrido con sus componentes |

## Notas de medición

- **Tiempo:** se mide con `time.perf_counter` sin `tracemalloc`, porque `tracemalloc` hace el código 2–4 veces más lento.
- **Memoria pico:** se mide con `tracemalloc` en una segunda pasada con la misma semilla, para las repeticiones 0–4 de cada instancia.
- **`f*` (referencia del error):** es la mejor ruta encontrada por cualquier algoritmo en todas las corridas de esa instancia.

## Informe final

- `informe/informe.tex` y `informe/informe.pdf` son el informe de entrega.

El informe compila con pdfLaTeX o XeLaTeX. En VS Code, con la extensión LaTeX Workshop, basta con guardar.

Probado con Python 3.11 (NumPy 2.4, pandas 3.0, SciPy 1.17, Matplotlib 3.10) y Chrome/Edge.
