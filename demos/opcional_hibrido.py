"""
PREGUNTA OPCIONAL - Híbrido ACO + 2-opt frente a sus componentes.
"""
import _comun  # noqa: F401
from _comun import leer, mostrar_figuras, titulo

titulo("Híbrido ACO+2opt vs ACO, HC y SA (Wilcoxon + Holm, mismo presupuesto)")
print(leer("hibrido.csv").to_string(index=False))
print("""
Lectura: el híbrido le gana a HC y SA, pero NO a ACO puro con n = 50 y 100,
porque la búsqueda local gasta 5n FEs por iteración y la colonia aprende menos.""")
mostrar_figuras(["fig6_hibrido"], "Opcional")
