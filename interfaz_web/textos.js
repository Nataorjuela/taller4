/* Textos claros para explicar cada algoritmo sin cargar la interfaz de matematicas. */
const INFO = {
  GA: {
    nombre: "Algoritmo genético", familia: "Prueba muchas rutas y mezcla las mejores", color: "var(--c-GA)", hex: "#2a78d6",
    idea: "Trabaja con muchas rutas a la vez. Conserva las mejores, combina partes de dos rutas buenas y hace pequeños cambios al azar. Puede mejorar con el tiempo, pero a veces rompe tramos que ya eran buenos.",
    formula: "\\[P_t \\xrightarrow{\\text{selección}} \\text{padres} \\xrightarrow{\\text{OX}} \\text{hijos} \\xrightarrow{\\text{mutación}} P_{t+1}\\]",
    simple: "Bueno para explorar muchas posibilidades. No fue el más fuerte en este TSP porque combinar rutas puede desordenar vecinos útiles.",
    como: "Úsalo para ver una estrategia de población: muchas rutas compiten y se cruzan.",
    params: { poblacion: "Cuántas rutas mantiene vivas", torneo: "Cuánta presión hay para escoger a los mejores",
      prob_cruce: "Qué tan seguido mezcla dos rutas", prob_mutacion: "Qué tan seguido hace cambios al azar", elite: "Cuántas rutas buenas protege" },
  },
  ACO: {
    nombre: "Colonia de hormigas", familia: "Aprende caminos buenos", color: "var(--c-ACO)", hex: "#eb6834",
    idea: "Construye rutas como si varias hormigas caminaran por la ciudad. Los caminos cortos reciben más señales, y las siguientes hormigas tienden a usarlos más.",
    formula: "\\[\\text{puntaje del camino}=\\text{señal acumulada}\\times\\text{cercanía}\\]",
    simple: "En los resultados del taller es el mejor en calidad y estabilidad. Tarda más, pero encuentra rutas muy buenas.",
    como: "Úsalo cuando te importa más la calidad de la ruta que el tiempo de ejecución.",
    params: { hormigas: "Cuántas rutas se construyen por ronda", alfa: "Peso de lo aprendido",
      beta: "Peso de elegir ciudades cercanas", rho: "Qué tan rápido se olvida lo viejo", Q: "Intensidad de la señal", elitistas: "Refuerzo extra a la mejor ruta" },
  },
  PSO: {
    nombre: "Enjambre de partículas", familia: "Sigue recuerdos individuales y grupales", color: "var(--c-PSO)", hex: "#1baf7a",
    idea: "Cada partícula recuerda su mejor intento y mira el mejor intento del grupo. Ajusta su posición tratando de acercarse a esas dos referencias.",
    formula: "\\[v \\leftarrow wv+c_1r_1(pbest-x)+c_2r_2(gbest-x),\\qquad \\text{ruta}=\\operatorname{argsort}(x)\\]",
    simple: "En este problema suele rendir mal: pequeños cambios internos pueden cambiar demasiado el orden de las ciudades.",
    como: "Úsalo para comparar que una idea buena en otros problemas no siempre encaja bien con rutas.",
    params: { particulas: "Cuántas soluciones prueba por ronda", w: "Cuánto conserva de su movimiento anterior", c1: "Peso de su propio recuerdo", c2: "Peso del mejor del grupo", vmax: "Límite de cambio por paso" },
  },
  HC: {
    nombre: "Ascenso de colinas", familia: "Mejora una ruta paso a paso", color: "var(--c-HC)", hex: "#eda100",
    idea: "Parte de una ruta y prueba cambios pequeños. Si el cambio acorta el camino, lo acepta. Si no, lo descarta. Cuando se atasca, vuelve a empezar.",
    formula: "\\[\\Delta=d(a,c)+d(b,d)-d(a,b)-d(c,d),\\qquad \\text{acepta si }\\Delta<0\\]",
    simple: "Es muy rápido y fácil de entender. Puede quedarse atrapado en rutas buenas, pero no excelentes.",
    como: "Úsalo cuando quieres una respuesta rápida y una ruta razonable.",
    params: { paciencia_factor: "Cuánto insiste antes de reiniciar desde otra ruta" },
  },
  SA: {
    nombre: "Temple simulado", familia: "Acepta algunos errores para escapar", color: "var(--c-SA)", hex: "#e87ba4",
    idea: "Se parece a HC, pero al inicio permite algunos cambios peores para escapar de rutas trabadas. Con el tiempo se vuelve más estricto.",
    formula: "\\[P(\\text{aceptar})=\\begin{cases}1,&\\Delta<0\\\\ e^{-\\Delta/T},&\\Delta\\ge 0\\end{cases}\\qquad T\\downarrow\\]",
    simple: "Suele ser un buen equilibrio: más lento que HC, pero con mejor capacidad para salir de bloqueos.",
    como: "Úsalo cuando quieres algo más robusto que HC sin pagar el costo de ACO.",
    params: { p0: "Qué tan dispuesto empieza a aceptar empeoramientos", ratio_final: "Qué tan frío termina", muestras_t0: "Intentos usados para calibrar el inicio" },
  },
  "ACO+2opt": {
    nombre: "Híbrido ACO + 2-opt", familia: "Hormigas + pulido local", color: "var(--c-ACO2)", hex: "#008300",
    idea: "Primero construye rutas como ACO y luego pule la mejor con cambios locales. Suena ideal, pero el pulido consume parte del presupuesto.",
    formula: "\\[\\text{ACO}\\rightarrow \\text{mejor hormiga}\\rightarrow \\text{2-opt con }5n\\text{ vecinos}\\]",
    simple: "Mejora frente a HC y SA, pero no supera al ACO puro en estos resultados.",
    como: "Úsalo para ver que mezclar métodos no siempre mejora todo: hay que repartir bien el presupuesto.",
    params: { hormigas: "Cuántas rutas construye por ronda", alfa: "Peso de lo aprendido", beta: "Peso de elegir ciudades cercanas", rho: "Olvido de señales viejas", Q: "Intensidad de la señal", elitistas: "Refuerzo a la mejor ruta", pasos_ls_factor: "Cuánto pulido local hace" },
  },
};
const ORDEN = ["GA", "ACO", "PSO", "HC", "SA"];

