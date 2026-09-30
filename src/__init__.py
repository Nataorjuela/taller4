"""Paquete con los cinco algoritmos del taller y utilidades comunes."""
from . import (ascenso_colinas, colonia_hormigas, enjambre_particulas, genetico,
               hibrido_aco_2opt, temple_simulado)

# Registro: nombre corto -> función optimizar(distancias, presupuesto, semilla, parametros)
ALGORITMOS = {
    "GA": genetico.optimizar,
    "ACO": colonia_hormigas.optimizar,
    "PSO": enjambre_particulas.optimizar,
    "HC": ascenso_colinas.optimizar,
    "SA": temple_simulado.optimizar,
    "ACO+2opt": hibrido_aco_2opt.optimizar,
}
