import requests
import re
from datetime import datetime

class WeatherService:
    """
    Service pour récupérer les informations météo aéronautiques (METAR).
    Utilise l'API publique de l'aviation (CheckWX ou similaire) ou une source de secours.
    """
    
    # Par défaut on utilise CheckWX (nécessite une clé, on met une clé de démo ou on mock)
    # Pour ce projet, on va utiliser une source publique sans clé si possible, 
    # ou un fallback sur la météo NOAA.
    
    BASE_URL = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/{station}.TXT"

    @classmethod
    def get_metar(cls, station="LFNE"):
        """
        Récupère le METAR brut pour une station donnée.
        """
        station = station.upper()
        try:
            response = requests.get(cls.BASE_URL.format(station=station), timeout=5)
            if response.status_code == 200:
                lines = response.text.splitlines()
                if len(lines) >= 2:
                    return lines[1] # Le METAR est sur la 2ème ligne
            return f"Indisponible pour {station}"
        except Exception as e:
            return f"Erreur météo: {str(e)}"

    @classmethod
    def parse_metar(cls, raw_metar):
        """
        Analyse simplifiée du METAR pour extraire le statut VFR/IFR.
        """
        if not raw_metar or "Indisponible" in raw_metar or "Erreur" in raw_metar:
            return {"status": "UNKNOWN", "color": "gray"}
            
        # Logique simplifiée : cherche 'CAVOK' ou des nuages bas
        # Regarde si VFR (Vis > 5km et Plafond > 1500ft)
        
        if "CAVOK" in raw_metar:
            return {"status": "VFR", "color": "green", "raw": raw_metar}
            
        # Détection basique de nuages bas (BKN005, OVC010...)
        low_clouds = re.search(r'(BKN|OVC)0(0[1-9]|1[0-5])', raw_metar)
        if low_clouds:
            return {"status": "IFR", "color": "red", "raw": raw_metar}
            
        # Détection basique de visibilité faible (0800, 1500...)
        low_vis = re.search(r' ([0-2][0-9]{3}) ', raw_metar)
        if low_vis and int(low_vis.group(1)) < 5000:
             return {"status": "IFR", "color": "red", "raw": raw_metar}

        return {"status": "VFR", "color": "green", "raw": raw_metar}
