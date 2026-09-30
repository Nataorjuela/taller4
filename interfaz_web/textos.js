/* Textos explicativos de cada algoritmo (idea sencilla + fórmula + parámetros). */
const INFO = {
  GA: {
    nombre: "Algoritmo genético", familia: "Poblacional · bioinspirado", color: "var(--c-GA)", hex: "#2a78d6",
    idea: "Imita la evolución: una población de rutas se reproduce. Las mejores tienen más chance de ser padres; los hijos combinan pedazos de ambos padres (cruce) y a veces sufren un cambio al azar (mutación).",
    formula: "Hijo = OX(padre₁, padre₂) → con prob. p<sub>m</sub>: invertir un tramo · padres elegidos por torneo de k",
    como: "Cada hijo nuevo cuesta 1 evaluación. Los 2 mejores (élite) pasan intactos: la mejor ruta nunca se pierde.",
    params: { poblacion: "Tamaño de la población (P)", torneo: "Individuos por torneo (k): más grande = más presión selectiva",
      prob_cruce: "Probabilidad de cruce OX", prob_mutacion: "Probabilidad de mutación por inversión", elite: "Mejores que pasan sin cambios" },
  },
  ACO: {
    nombre: "Colonia de hormigas", familia: "Poblacional · bioinspirado", color: "var(--c-ACO)", hex: "#eb6834",
    idea: "Cada hormiga construye una ruta ciudad por ciudad. Prefiere ciudades cercanas (visibilidad 1/d) y tramos con mucha feromona (lo que aprendió la colonia). Las rutas cortas dejan más feromona y la feromona vieja se evapora.",
    formula: "P(i→j) = τ<sub>ij</sub><sup>α</sup> η<sub>ij</sub><sup>β</sup> / Σ τ<sub>il</sub><sup>α</sup> η<sub>il</sub><sup>β</sup>, &nbsp; η = 1/d &nbsp;·&nbsp; τ ← (1−ρ)τ + Σ Q/L<sub>k</sub>",
    como: "Cada ruta construida por una hormiga cuesta 1 evaluación. Es el único que usa las distancias para CONSTRUIR la ruta, por eso arranca muy bien.",
    params: { hormigas: "Número de hormigas m (vacío = n)", alfa: "α: peso de la feromona", beta: "β: peso de la cercanía",
      rho: "ρ: evaporación (olvido)", Q: "Q: cantidad de feromona depositada", elitistas: "Peso extra de la mejor ruta histórica" },
  },
  PSO: {
    nombre: "Enjambre de partículas", familia: "Poblacional · bioinspirado", color: "var(--c-PSO)", hex: "#1baf7a",
    idea: "Una bandada de pájaros: cada partícula recuerda su mejor posición y conoce la mejor del grupo, y ajusta su vuelo hacia ambas. La ruta se obtiene ORDENANDO los números del vector (claves aleatorias).",
    formula: "v ← w·v + c₁r₁(p − x) + c₂r₂(g − x) &nbsp;·&nbsp; x ← x + v &nbsp;·&nbsp; ruta = argsort(x)",
    como: "Cada partícula evaluada cuesta 1 evaluación. Un cambio pequeño en x puede reordenar muchas ciudades: por eso le va mal en el TSP.",
    params: { particulas: "Número de partículas S", w: "Inercia w", c1: "c₁: atracción a su mejor posición", c2: "c₂: atracción a la mejor del enjambre", vmax: "Velocidad máxima" },
  },
  HC: {
    nombre: "Ascenso de colinas", familia: "Trayectoria única", color: "var(--c-HC)", hex: "#eda100",
    idea: "Una sola ruta que va probando cambios pequeños (2-opt: descruzar dos tramos). Si el cambio acorta la ruta se queda con él; si no, lo descarta. Si se atasca, reinicia desde otra ruta al azar.",
    formula: "Δ = d(a,c) + d(b,d) − d(a,b) − d(c,d) &nbsp;·&nbsp; aceptar si Δ < 0",
    como: "Cada vecino probado cuesta 1 evaluación, calculada con Δ en tiempo O(1): por eso es rapidísimo.",
    params: { paciencia_factor: "Intentos sin mejora antes de reiniciar = factor · n(n−1)/2" },
  },
  SA: {
    nombre: "Temple simulado", familia: "Trayectoria única", color: "var(--c-SA)", hex: "#e87ba4",
    idea: "Como HC, pero a veces acepta un cambio que EMPEORA la ruta, para poder salir de hoyos (óptimos locales). Al principio (caliente) acepta muchos empeoramientos; al final (frío) casi ninguno.",
    formula: "P(aceptar) = e<sup>−Δ/T</sup> si Δ > 0 &nbsp;·&nbsp; T<sub>0</sub> = −Δ̄ / ln p<sub>0</sub> &nbsp;·&nbsp; T ← α·T",
    como: "Usa el MISMO vecino 2-opt que HC: la única diferencia es la regla de aceptación. Mire la curva: baja lento al inicio y cae en picada al enfriarse.",
    params: { p0: "Prob. inicial de aceptar un empeoramiento típico", ratio_final: "T final = T₀ · ratio", muestras_t0: "Vecinos usados para calibrar T₀" },
  },
  "ACO+2opt": {
    nombre: "Híbrido ACO + 2-opt", familia: "Híbrido (opcional)", color: "var(--c-ACO2)", hex: "#008300",
    idea: "La colonia construye rutas y la mejor hormiga de cada iteración se pule con búsqueda local 2-opt antes de dejar feromona.",
    formula: "ACO + (5n propuestas 2-opt sobre la mejor hormiga) — mismo presupuesto total de evaluaciones",
    como: "La búsqueda local gasta evaluaciones, así que la colonia hace menos iteraciones.",
    params: { hormigas: "Número de hormigas (vacío = n)", alfa: "α", beta: "β", rho: "ρ", Q: "Q", elitistas: "Peso de la mejor", pasos_ls_factor: "Pasos 2-opt por iteración = factor · n" },
  },
};
const ORDEN = ["GA", "ACO", "PSO", "HC", "SA"];
