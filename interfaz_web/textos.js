/* Textos claros para explicar cada algoritmo sin cargar la interfaz de matematicas. */
const INFO = {
  GA: {
    nombre: "Algoritmo genetico", familia: "Prueba muchas rutas y mezcla las mejores", color: "var(--c-GA)", hex: "#2a78d6",
    idea: "Trabaja con muchas rutas a la vez. Conserva las mejores, combina partes de dos rutas buenas y hace pequenos cambios al azar. Puede mejorar con el tiempo, pero a veces rompe tramos que ya eran buenos.",
    simple: "Bueno para explorar muchas posibilidades. No fue el mas fuerte en este TSP porque combinar rutas puede desordenar vecinos utiles.",
    como: "Usalo para ver una estrategia de poblacion: muchas rutas compiten y se cruzan.",
    params: { poblacion: "Cuantas rutas mantiene vivas", torneo: "Cuanta presion hay para escoger a los mejores",
      prob_cruce: "Que tan seguido mezcla dos rutas", prob_mutacion: "Que tan seguido hace cambios al azar", elite: "Cuantas rutas buenas protege" },
  },
  ACO: {
    nombre: "Colonia de hormigas", familia: "Aprende caminos buenos", color: "var(--c-ACO)", hex: "#eb6834",
    idea: "Construye rutas como si varias hormigas caminaran por la ciudad. Los caminos cortos reciben mas senales, y las siguientes hormigas tienden a usarlos mas.",
    simple: "En los resultados del taller es el mejor en calidad y estabilidad. Tarda mas, pero encuentra rutas muy buenas.",
    como: "Usalo cuando te importa mas la calidad de la ruta que el tiempo de ejecucion.",
    params: { hormigas: "Cuantas rutas se construyen por ronda", alfa: "Peso de lo aprendido",
      beta: "Peso de elegir ciudades cercanas", rho: "Que tan rapido se olvida lo viejo", Q: "Intensidad de la senal", elitistas: "Refuerzo extra a la mejor ruta" },
  },
  PSO: {
    nombre: "Enjambre de particulas", familia: "Sigue recuerdos individuales y grupales", color: "var(--c-PSO)", hex: "#1baf7a",
    idea: "Cada particula recuerda su mejor intento y mira el mejor intento del grupo. Ajusta su posicion tratando de acercarse a esas dos referencias.",
    simple: "En este problema suele rendir mal: pequenos cambios internos pueden cambiar demasiado el orden de las ciudades.",
    como: "Usalo para comparar que una idea buena en otros problemas no siempre encaja bien con rutas.",
    params: { particulas: "Cuantas soluciones prueba por ronda", w: "Cuanto conserva de su movimiento anterior", c1: "Peso de su propio recuerdo", c2: "Peso del mejor del grupo", vmax: "Limite de cambio por paso" },
  },
  HC: {
    nombre: "Ascenso de colinas", familia: "Mejora una ruta paso a paso", color: "var(--c-HC)", hex: "#eda100",
    idea: "Parte de una ruta y prueba cambios pequenos. Si el cambio acorta el camino, lo acepta. Si no, lo descarta. Cuando se atasca, vuelve a empezar.",
    simple: "Es muy rapido y facil de entender. Puede quedarse atrapado en rutas buenas, pero no excelentes.",
    como: "Usalo cuando quieres una respuesta rapida y una ruta razonable.",
    params: { paciencia_factor: "Cuanto insiste antes de reiniciar desde otra ruta" },
  },
  SA: {
    nombre: "Temple simulado", familia: "Acepta algunos errores para escapar", color: "var(--c-SA)", hex: "#e87ba4",
    idea: "Se parece a HC, pero al inicio permite algunos cambios peores para escapar de rutas trabadas. Con el tiempo se vuelve mas estricto.",
    simple: "Suele ser un buen equilibrio: mas lento que HC, pero con mejor capacidad para salir de bloqueos.",
    como: "Usalo cuando quieres algo mas robusto que HC sin pagar el costo de ACO.",
    params: { p0: "Que tan dispuesto empieza a aceptar empeoramientos", ratio_final: "Que tan frio termina", muestras_t0: "Intentos usados para calibrar el inicio" },
  },
  "ACO+2opt": {
    nombre: "Hibrido ACO + 2-opt", familia: "Hormigas + pulido local", color: "var(--c-ACO2)", hex: "#008300",
    idea: "Primero construye rutas como ACO y luego pule la mejor con cambios locales. Suena ideal, pero el pulido consume parte del presupuesto.",
    simple: "Mejora frente a HC y SA, pero no supera al ACO puro en estos resultados.",
    como: "Usalo para ver que mezclar metodos no siempre mejora todo: hay que repartir bien el presupuesto.",
    params: { hormigas: "Cuantas rutas construye por ronda", alfa: "Peso de lo aprendido", beta: "Peso de elegir ciudades cercanas", rho: "Olvido de senales viejas", Q: "Intensidad de la senal", elitistas: "Refuerzo a la mejor ruta", pasos_ls_factor: "Cuanto pulido local hace" },
  },
};
const ORDEN = ["GA", "ACO", "PSO", "HC", "SA"];
