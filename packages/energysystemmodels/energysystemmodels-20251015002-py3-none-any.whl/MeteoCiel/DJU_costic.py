def DJU_costic(Tmin, Tmax, base_chauffage=18, base_refroidissement=23):
    dju_chauffage = 0
    dju_rafraichissement = 0
    
    if Tmax <= base_chauffage:
        dju_chauffage = base_chauffage - (Tmin + Tmax) / 2
        
    elif Tmin >= base_refroidissement:
        dju_rafraichissement = (Tmin + Tmax) / 2 - base_refroidissement
        
    else:
        if Tmin < base_chauffage and Tmax > base_chauffage:
            a = Tmax - Tmin
            b = (base_chauffage - Tmin) / a
            dju_chauffage = a * b * (0.08 + 0.42 * b)
        
        if Tmax > base_refroidissement and Tmin < base_refroidissement:
            a = Tmax - base_refroidissement
            b = a / (Tmax - Tmin)
            dju_rafraichissement = a * b * (0.08 + 0.42 * b)
        
    return dju_chauffage, dju_rafraichissement
