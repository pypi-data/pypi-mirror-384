from Facture.SONALGAZ_gaz import input_Contrat, input_Facture, Sonalgaz_Gaz

# Test avec les unités thermies
contrat = input_Contrat(
    code_tarif="11",
    DMD_thermie_h=40000  # en thermies/h
)

facture = input_Facture(
    start="2025-01-01",
    end="2025-01-31",
    thermies=23177817.83,  # en thermies
    DMA_thermie_h=37079  # en thermies/h
)

calc = Sonalgaz_Gaz(contrat, facture)
calc.calculate()
print(calc.df)
calc.plot()
calc.plot_detail()