"""
Service de recuperation METAR/TAF depuis les APIs publiques.
Utilise l'API Aviation Weather Center (AWC) de la NOAA.
"""
import requests
from datetime import datetime, timedelta
from django.core.cache import cache
import xml.etree.ElementTree as ET
import re


# URL de l'API AWC NOAA (gratuit, pas de cle API requise)
AWC_METAR_URL = "https://aviationweather.gov/api/data/metar"
AWC_TAF_URL = "https://aviationweather.gov/api/data/taf"

# Cache duration (en secondes)
METAR_CACHE_DURATION = 300  # 5 minutes
TAF_CACHE_DURATION = 1800   # 30 minutes


def get_metar(icao_code):
    """
    Recupere le METAR pour un aeroport donne.

    Args:
        icao_code: Code OACI de l'aeroport (ex: LFPG, LFBO)

    Returns:
        dict avec les donnees METAR ou None si erreur
    """
    icao_code = icao_code.upper().strip()
    cache_key = f"metar_{icao_code}"

    # Verifier le cache
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        response = requests.get(
            AWC_METAR_URL,
            params={
                'ids': icao_code,
                'format': 'json',
                'taf': 'false',
                'hours': 2,
            },
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        if data and len(data) > 0:
            metar_data = data[0]
            result = parse_metar_json(metar_data)
            cache.set(cache_key, result, METAR_CACHE_DURATION)
            return result

        return None

    except Exception as e:
        print(f"Erreur recuperation METAR {icao_code}: {e}")
        return None


def get_taf(icao_code):
    """
    Recupere le TAF pour un aeroport donne.

    Args:
        icao_code: Code OACI de l'aeroport (ex: LFPG, LFBO)

    Returns:
        dict avec les donnees TAF ou None si erreur
    """
    icao_code = icao_code.upper().strip()
    cache_key = f"taf_{icao_code}"

    # Verifier le cache
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        response = requests.get(
            AWC_TAF_URL,
            params={
                'ids': icao_code,
                'format': 'json',
            },
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        if data and len(data) > 0:
            taf_data = data[0]
            result = parse_taf_json(taf_data)
            cache.set(cache_key, result, TAF_CACHE_DURATION)
            return result

        return None

    except Exception as e:
        print(f"Erreur recuperation TAF {icao_code}: {e}")
        return None


def parse_metar_json(data):
    """Parse les donnees METAR JSON de l'AWC."""
    result = {
        'raw': data.get('rawOb', ''),
        'icao': data.get('icaoId', ''),
        'observation_time': data.get('obsTime', ''),
        'temp': data.get('temp'),
        'dewpoint': data.get('dewp'),
        'wind_dir': data.get('wdir'),
        'wind_speed': data.get('wspd'),
        'wind_gust': data.get('wgst'),
        'visibility': data.get('visib'),
        'altimeter': data.get('altim'),
        'clouds': data.get('clouds', []),
        'weather': data.get('wxString', ''),
        'flight_category': data.get('fltcat', ''),
        'name': data.get('name', ''),
    }

    # Determiner la condition VFR/MVFR/IFR/LIFR
    result['is_vfr'] = result['flight_category'] in ['VFR', 'MVFR']
    result['is_ifr'] = result['flight_category'] in ['IFR', 'LIFR']

    return result


def parse_taf_json(data):
    """Parse les donnees TAF JSON de l'AWC."""
    result = {
        'raw': data.get('rawTAF', ''),
        'icao': data.get('icaoId', ''),
        'issue_time': data.get('issueTime', ''),
        'valid_from': data.get('validTimeFrom', ''),
        'valid_to': data.get('validTimeTo', ''),
        'forecasts': [],
    }

    # Parser les periodes de prevision si disponibles
    if 'fcsts' in data:
        for fcst in data['fcsts']:
            period = {
                'time_from': fcst.get('timeFrom', ''),
                'time_to': fcst.get('timeTo', ''),
                'wind_dir': fcst.get('wdir'),
                'wind_speed': fcst.get('wspd'),
                'wind_gust': fcst.get('wgst'),
                'visibility': fcst.get('visib'),
                'clouds': fcst.get('clouds', []),
                'weather': fcst.get('wxString', ''),
            }
            result['forecasts'].append(period)

    return result


def get_weather_for_airports(icao_codes):
    """
    Recupere la meteo pour plusieurs aeroports.

    Args:
        icao_codes: Liste de codes OACI

    Returns:
        dict {icao: {metar: {...}, taf: {...}}}
    """
    result = {}
    for icao in icao_codes:
        result[icao] = {
            'metar': get_metar(icao),
            'taf': get_taf(icao),
        }
    return result


def interpret_flight_conditions(metar_data):
    """
    Interprete les conditions de vol a partir des donnees METAR.

    Returns:
        dict avec les recommandations
    """
    if not metar_data:
        return {
            'status': 'UNKNOWN',
            'message': 'Donnees meteo non disponibles',
            'color': 'gray',
            'can_fly_vfr': None,
        }

    flight_cat = metar_data.get('flight_category', '')

    conditions = {
        'VFR': {
            'status': 'VFR',
            'message': 'Conditions VFR - Vol a vue autorise',
            'color': 'green',
            'can_fly_vfr': True,
        },
        'MVFR': {
            'status': 'MVFR',
            'message': 'VFR Marginal - Prudence recommandee',
            'color': 'blue',
            'can_fly_vfr': True,
        },
        'IFR': {
            'status': 'IFR',
            'message': 'Conditions IFR - Vol a vue deconseille',
            'color': 'red',
            'can_fly_vfr': False,
        },
        'LIFR': {
            'status': 'LIFR',
            'message': 'IFR Bas - Vol a vue interdit',
            'color': 'purple',
            'can_fly_vfr': False,
        },
    }

    result = conditions.get(flight_cat, {
        'status': 'UNKNOWN',
        'message': 'Conditions inconnues',
        'color': 'gray',
        'can_fly_vfr': None,
    })

    # Ajouter les details du vent
    wind_speed = metar_data.get('wind_speed', 0) or 0
    wind_gust = metar_data.get('wind_gust', 0) or 0

    if wind_gust >= 25 or wind_speed >= 20:
        result['wind_warning'] = 'Vent fort - Attention atterrissages'

    if wind_gust >= 30 or wind_speed >= 25:
        result['wind_warning'] = 'Rafales fortes - Vol deconseille eleves'
        if result.get('can_fly_vfr'):
            result['can_fly_vfr'] = 'experienced_only'

    return result


# Aeroports francais courants
COMMON_FRENCH_AIRPORTS = [
    ('LFPG', 'Paris CDG'),
    ('LFPO', 'Paris Orly'),
    ('LFBO', 'Toulouse'),
    ('LFLL', 'Lyon'),
    ('LFML', 'Marseille'),
    ('LFBD', 'Bordeaux'),
    ('LFMN', 'Nice'),
    ('LFRS', 'Nantes'),
    ('LFSB', 'Bale-Mulhouse'),
    ('LFST', 'Strasbourg'),
    ('LFPB', 'Le Bourget'),
    ('LFPT', 'Pontoise'),
    ('LFPN', 'Toussus'),
    ('LFPM', 'Melun'),
    ('LFPA', 'Persan'),
]
