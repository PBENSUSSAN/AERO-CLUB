from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .services import (
    get_metar, get_taf, get_weather_for_airports,
    interpret_flight_conditions, COMMON_FRENCH_AIRPORTS
)


@login_required
def weather_dashboard(request):
    """Page principale meteo avec METAR/TAF."""
    home_airport = request.GET.get('icao', 'LFPT')  # Pontoise par defaut

    metar = get_metar(home_airport)
    taf = get_taf(home_airport)
    conditions = interpret_flight_conditions(metar)

    airports = COMMON_FRENCH_AIRPORTS

    return render(request, 'meteo/dashboard.html', {
        'home_airport': home_airport,
        'metar': metar,
        'taf': taf,
        'conditions': conditions,
        'airports': airports,
    })


@login_required
def metar_api(request, icao):
    """API JSON pour recuperer le METAR d'un aeroport."""
    metar = get_metar(icao)
    if metar:
        conditions = interpret_flight_conditions(metar)
        return JsonResponse({
            'success': True,
            'icao': icao,
            'metar': metar,
            'conditions': conditions,
        })
    return JsonResponse({
        'success': False,
        'error': f'METAR non disponible pour {icao}',
    }, status=404)


@login_required
def taf_api(request, icao):
    """API JSON pour recuperer le TAF d'un aeroport."""
    taf = get_taf(icao)
    if taf:
        return JsonResponse({
            'success': True,
            'icao': icao,
            'taf': taf,
        })
    return JsonResponse({
        'success': False,
        'error': f'TAF non disponible pour {icao}',
    }, status=404)


@login_required
def multi_airport_weather(request):
    """API pour recuperer la meteo de plusieurs aeroports."""
    icao_codes = request.GET.get('airports', '').split(',')
    icao_codes = [c.strip().upper() for c in icao_codes if c.strip()]

    if not icao_codes:
        return JsonResponse({
            'success': False,
            'error': 'Aucun code OACI fourni',
        }, status=400)

    weather_data = get_weather_for_airports(icao_codes)

    for icao, data in weather_data.items():
        if data.get('metar'):
            data['conditions'] = interpret_flight_conditions(data['metar'])

    return JsonResponse({
        'success': True,
        'airports': weather_data,
    })


@login_required
def weather_widget(request):
    """Widget meteo compact pour integration dans d'autres pages."""
    icao = request.GET.get('icao', 'LFPT')
    metar = get_metar(icao)
    conditions = interpret_flight_conditions(metar)

    return render(request, 'meteo/widget.html', {
        'icao': icao,
        'metar': metar,
        'conditions': conditions,
    })
