from Facture.ATR_Transport_Distribution import input_Contrat, input_Facture, input_Tarif, ATR_calculation

if __name__ == "__main__":
    contrat = input_Contrat(type_tarif_acheminement='T4',CJN_MWh_j=93,modulation_MWh_j=20.217, CAR_MWh=6801.540, profil="P019", station_meteo="PARIS-MONTSOURIS", reseau_transport="GRTgaz", niv_tarif_region=2)
    facture = input_Facture(start="2024-06-01", end="2024-06-30", kWh_total=0)
    tarif = input_Tarif(prix_kWh=0.03171+0.00571)

    atr = ATR_calculation(contrat, facture, tarif)
    atr.calculate()
    print(atr.df)
    print(atr.df_transport)
    print(atr.df_distribution)
    print(atr.df_taxes_contributions)
    print(atr.df_molecule)
    print(atr.df_annuel)

    print("atr.CJN_MWh_j",atr.CJN)
    #zi
    print("art.cofficient_zi", atr.zi)
    #coef A
    print("atr.cofficient_A", atr.coef_A)

    print("coef_stockage", atr.coef_stockage)

   