from django.shortcuts import render
from members.models import Member
from .weather_service import WeatherService

def home(request):
    """
    Page d'accueil du site avec météo aéronautique.
    """
    # Récupérer les instructeurs pour la section Équipe
    instructors = Member.objects.filter(is_instructor=True).select_related('user')
    
    # Récupérer la météo (LFNE par défaut - Salon Eyguières)
    raw_metar = WeatherService.get_metar("LFNE")
    weather = WeatherService.parse_metar(raw_metar)

    return render(request, 'core/index.html', {
        'instructors': instructors,
        'weather': weather
    })
