from Facture.SONALGAZ_Elec import input_Contrat, input_Facture, Sonalgaz_Elec


# Plus besoin de spécifier la tension
contrat = input_Contrat(
    code_tarif="42",  # Code 41,42,43,44 => HTA automatiquement
    PMD_kW=80
)

facture = input_Facture(
    start="2025-01-01",
    end="2025-01-31",
    kWh_pointe=3174.90,
    kWh_hors_pointe=10215.24,
    #kWh_pleine=300000,
    #kWh_nuit=200000,
    PMA_kW=37, #"puissance maximale atteinte"
    kvarh_reactif=11784.40 # Sera comparé à 0.5 * (3174.90 + 10215.24)
)

calc = Sonalgaz_Elec(contrat, facture)
calc.calculate()
print(calc.df)
calc.plot()  # Pour le graphique en donut
calc.plot_detail()  # Pour le détail des composantes