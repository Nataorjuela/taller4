# Taller 4 – Comparación de metaheurísticas en el TSP

Comparación reproducible de cinco métodos de optimización (Algoritmo genético, Colonia de hormigas,
Enjambre de partículas, Ascenso de colinas y Temple simulado) sobre el problema del viajante,
con un presupuesto igual de evaluaciones de la función objetivo (FEs).
Incluye también el híbrido opcional **ACO + 2-opt**.

## Instalación

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

Probado con Python 3.11 (NumPy 2.4, pandas 3.0, SciPy 1.17, Matplotlib 3.10).

## Ejecución

```bash
python -m pytest pruebas -q        # 1) pruebas (o: python pruebas/test_algoritmos.py)
python experimentos/piloto.py                                 # 2) fase piloto (opcional, ≈ 3 min)
python ejecutar_experimentos.py --config configuracion.json   # 3) experimento completo
python experimentos/analizar_resultados.py --config configuracion.json   # 4) tablas y figuras
```

El experimento completo (2 700 corridas) tarda unos 35–40 minutos con 2 procesos.
Cada corrida se guarda apenas termina en `resultados/corridas.jsonl`; si se interrumpe,
al relanzar el comando continúa donde iba. Para una prueba rápida, reduzca `repeticiones`
y `presupuestos` en `configuracion.json` (y cambie `carpeta_resultados`).

## Semillas (reproducibilidad)

* Instancias: semillas públicas **101, 102, 103, 104, 105**; la semilla real de cada instancia es
  `SeedSequence([semilla_publica, n])`.
* Corridas: `SeedSequence([2026, n, instancia, repeticion])`, **la misma para todos los algoritmos**
  (comparaciones emparejadas).
* Fase piloto: instancias 901, 902, 903 (distintas de las del experimento final).

## Estructura

```
src/                       implementación modular
  tsp.py                   instancias, distancias, función objetivo, Evaluador (conteo de FEs)
  vecindad.py              vecino 2-opt compartido por HC y SA
  interfaz.py              envoltorio común: semilla, tiempo, memoria, verificación
  genetico.py              GA: torneo, cruce OX, mutación por inversión, elitismo
  colonia_hormigas.py      ACO: Ant System elitista
  enjambre_particulas.py   PSO con claves aleatorias
  ascenso_colinas.py       HC con reinicios
  temple_simulado.py       SA con criterio de Metropolis y enfriamiento geométrico
  hibrido_aco_2opt.py      híbrido opcional
  experimento.py           semillas y ejecución de una corrida
experimentos/
  piloto.py                ajuste de parámetros en instancias separadas
  analizar_resultados.py   tablas, figuras y pruebas estadísticas
pruebas/test_algoritmos.py pruebas automáticas
ejecutar_experimentos.py   comando principal
configuracion.json         todos los parámetros del experimento
resultados/                CSV originales y tablas resumidas (.csv y .tex)
figuras/                   gráficas (.png y .pdf)
informe/                   informe.tex / informe.pdf (máx. 8 páginas)
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

* El tiempo se mide con `time.perf_counter` sin `tracemalloc` (que hace el código 2–4 veces más lento).
* La memoria pico se mide con `tracemalloc` en una segunda pasada con la misma semilla para las
  repeticiones 0–4 de cada instancia (`repeticiones_con_memoria` en la configuración).
  En las demás filas la columna `memoria` queda vacía.
* `f*` (referencia del error) es la mejor ruta encontrada por cualquier algoritmo en todas las corridas
  de esa instancia.

## Guía explicada

`guia/guia_taller4.tex` es un solo archivo LaTeX autocontenido (solo necesita la carpeta `figuras/`)
con la teoría, el porqué de cada decisión y la solución de cada punto; `guia/guia_taller4.pdf` es su versión compilada.
Compila con pdfLaTeX o XeLaTeX (en VS Code con LaTeX Workshop basta con guardar).
`informe/informe.tex` es el informe de 6 páginas (también autocontenido).
