from PyQt5.QtWidgets import *

import os
import sys

# Ajout du chemin vers le dossier parent pour importer les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import du module CalculatorWindow depuis PyqtSimulator
from PyqtSimulator.calc_window import CalculatorWindow

# Initialisation de l'application PyQt
app = QApplication(sys.argv)

# Définition du style de l'application
app.setStyle('Fusion')

# Création de la fenêtre de la calculatrice
wnd = CalculatorWindow()

# Affichage de la fenêtre
wnd.show()

# Exécution de l'application
sys.exit(app.exec_())
