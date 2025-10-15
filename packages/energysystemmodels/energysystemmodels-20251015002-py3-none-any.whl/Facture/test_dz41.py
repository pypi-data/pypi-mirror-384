from Facture.SONALGAZ_Elec import input_Contrat, input_Facture, Sonalgaz_Elec


# Plus besoin de spécifier la tension
contrat = input_Contrat(
    code_tarif="41",  # Code 41,42,43,44 => HTA automatiquement
    PMD_kW=1000
)

facture = input_Facture(
    start="2025-03-01",
    end="2025-03-31",
    kWh_pointe=20585.00,
    #kWh_hors_pointe=10215.24,
    kWh_pleine=63963.00,
    kWh_nuit=40091.00, #heure creuse

    PMA_kW=367, #"puissance maximale atteinte"
    kvarh_reactif=50827.00 # Sera comparé à 0.5 * (3174.90 + 10215.24)
)

calc = Sonalgaz_Elec(contrat, facture)
calc.calculate()
print(calc.df)
calc.plot()  # Pour le graphique en donut
calc.plot_detail()  # Pour le détail des composantes