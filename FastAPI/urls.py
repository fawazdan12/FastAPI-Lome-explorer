from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views
from . import geolocation_views

# Configuration du routeur pour les ViewSets
router = DefaultRouter()
router.register(r'lieux', views.LieuViewSet)
router.register(r'evenements', views.EvenementViewSet)
router.register(r'avis-lieux', views.AvisLieuViewSet)
router.register(r'avis-evenements', views.AvisEvenementViewSet)

# URLs de l'application
urlpatterns = [
    # Authentification
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # ViewSets automatiques via le routeur
    path('api/', include(router.urls)),
    
    # Statistiques et données publiques
    path('stats/', views.statistiques, name='statistiques'),
    path('lieux-populaires/', views.lieux_populaires, name='lieux_populaires'),
    path('evenements-tendances/', views.evenements_tendances, name='evenements_tendances'),
    path('donnees-lome/', views.donnees_lome, name='donnees_lome'),
    
    # Services de géolocalisation
    path('geo/detect-location/', geolocation_views.detect_user_location, name='detect_location'),
    path('geo/geocode/', geolocation_views.geocode_address, name='geocode_address'),
    path('geo/reverse-geocode/', geolocation_views.reverse_geocode, name='reverse_geocode'),
    path('geo/lieux-proximite/', geolocation_views.lieux_proximite, name='lieux_proximite'),
    path('geo/evenements-proximite/', geolocation_views.evenements_proximite, name='evenements_proximite'),
    path('geo/suggestions/', geolocation_views.suggestions_adresses, name='suggestions_adresses'),
    path('geo/distance/', geolocation_views.calculate_distance, name='calculate_distance'),
    path('geo/quartiers-lome/', geolocation_views.quartiers_lome, name='quartiers_lome'),
    path('geo/validate-lome/', geolocation_views.validate_lome_location, name='validate_lome_location'),
    path('geo/ip-location/', geolocation_views.ip_location, name='ip_location'),
    path('geo/map-data/', geolocation_views.map_data, name='map_data'),
]

# URLs générées automatiquement par le routeur :
# 
# LIEUX:
# GET    /api/lieux/                           - Liste des lieux
# POST   /api/lieux/                           - Créer un lieu
# GET    /api/lieux/{id}/                      - Détails d'un lieu
# PUT    /api/lieux/{id}/                      - Modifier un lieu
# DELETE /api/lieux/{id}/                      - Supprimer un lieu
# GET    /api/lieux/{id}/evenements/           - Événements du lieu
# GET    /api/lieux/{id}/avis/                 - Avis du lieu
# GET    /api/lieux/recherche_proximite/       - Recherche par proximité
#
# EVENEMENTS:
# GET    /api/evenements/                      - Liste des événements
# POST   /api/evenements/                      - Créer un événement
# GET    /api/evenements/{id}/                 - Détails d'un événement
# PUT    /api/evenements/{id}/                 - Modifier un événement
# DELETE /api/evenements/{id}/                 - Supprimer un événement
# GET    /api/evenements/{id}/avis/            - Avis de l'événement
# GET    /api/evenements/aujourd_hui/          - Événements d'aujourd'hui
# GET    /api/evenements/cette_semaine/        - Événements de cette semaine
#
# AVIS LIEUX:
# GET    /api/avis-lieux/                      - Liste des avis de lieux
# POST   /api/avis-lieux/                      - Créer un avis de lieu
# GET    /api/avis-lieux/{id}/                 - Détails d'un avis de lieu
# PUT    /api/avis-lieux/{id}/                 - Modifier un avis de lieu
# DELETE /api/avis-lieux/{id}/                 - Supprimer un avis de lieu
#
# AVIS EVENEMENTS:
# GET    /api/avis-evenements/                 - Liste des avis d'événements
# POST   /api/avis-evenements/                 - Créer un avis d'événement
# GET    /api/avis-evenements/{id}/            - Détails d'un avis d'événement
# PUT    /api/avis-evenements/{id}/            - Modifier un avis d'événement
# DELETE /api/avis-evenements/{id}/            - Supprimer un avis d'événement