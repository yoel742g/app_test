import pandas as pd
import numpy as np
def verbrauch(jahresverbrauch):

    dateiname_ods = 'Haushaltswerte.ods'


    df = pd.read_excel(dateiname_ods, engine='odf', index_col=0)
    monate_tage = {
        'Januar': 31,
        'Februar': 28,
        'März': 31,
        'April': 30,
        'Mai': 31,
        'Juni': 30,
        'Juli': 31,
        'August': 31,
        'September': 30,
        'Oktober': 31,
        'November': 30,
        'Dezember': 31
    }

    jahres_profil_werte = []


    for monat, tage in monate_tage.items():

        tagesprofil = df[monat].values

        for _ in range(tage):
            jahres_profil_werte.extend(tagesprofil)

    jahres_profil_werte = np.array(jahres_profil_werte)
    summe_profil = np.sum(jahres_profil_werte)


    verbrauch_15min_array = jahresverbrauch * (jahres_profil_werte / summe_profil)

    return verbrauch_15min_array

