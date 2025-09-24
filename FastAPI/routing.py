from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # WebSocket général pour les notifications d'événements
    path('ws/events/', consumers.EventNotificationConsumer.as_asgi()),
    
    # WebSocket pour les notifications personnelles (utilisateur authentifié)
    path('ws/personal/', consumers.PersonalNotificationConsumer.as_asgi()),
    
    # WebSocket basé sur la localisation
    path('ws/location/<str:latitude>/<str:longitude>/', consumers.LocationBasedConsumer.as_asgi()),
    path('ws/location/<str:latitude>/<str:longitude>/<int:radius>/', consumers.LocationBasedConsumer.as_asgi()),
]