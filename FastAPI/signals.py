from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Evenement, Lieu, AvisEvenement, AvisLieu
from .serializers import EvenementListSerializer, LieuListSerializer
from .geolocation_services import GeolocationService
import logging

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


def send_to_websocket(group_name, message_type, data):
    """Fonction utilitaire pour envoyer des messages WebSocket"""
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': message_type,
                **data
            }
        )
    except Exception as e:
        logger.error(f"Erreur envoi WebSocket vers {group_name}: {e}")


@receiver(post_save, sender=Evenement)
def evenement_created_or_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création/modification d'un événement"""
    
    # Sérialiser l'événement
    event_data = EvenementListSerializer(instance).data
    
    if created:
        # Nouvel événement créé
        logger.info(f"Nouvel événement créé: {instance.nom}")
        
        # Notification globale
        send_to_websocket(
            'events_notifications',
            'new_event_notification',
            {'event_data': event_data}
        )
        
        # Notifications basées sur la localisation
        send_location_based_notifications(instance, event_data, 'new_event')
        
        # Notification par catégorie si applicable
        if hasattr(instance.lieu, 'categorie') and instance.lieu.categorie:
            category_group = f"category_{instance.lieu.categorie.lower().replace(' ', '_')}"
            send_to_websocket(
                category_group,
                'new_event_notification',
                {'event_data': event_data}
            )
    
    else:
        # Événement modifié
        logger.info(f"Événement modifié: {instance.nom}")
        
        send_to_websocket(
            'events_notifications',
            'event_updated_notification',
            {'event_data': event_data}
        )
        
        send_location_based_notifications(instance, event_data, 'event_updated')


def send_location_based_notifications(evenement, event_data, notification_type):
    """Envoyer des notifications basées sur la localisation"""
    try:
        # Calculer les zones géographiques concernées
        lieu = evenement.lieu
        lat_zone = int(float(lieu.latitude) * 100)
        lng_zone = int(float(lieu.longitude) * 100)
        
        # Envoyer à la zone principale
        location_group = f'location_{lat_zone}_{lng_zone}'
        send_to_websocket(
            location_group,
            f'{notification_type}_notification',
            {'event_data': event_data}
        )
        
        # Envoyer aux zones adjacentes (rayon élargi)
        for lat_offset in [-1, 0, 1]:
            for lng_offset in [-1, 0, 1]:
                if lat_offset == 0 and lng_offset == 0:
                    continue  # Zone principale déjà traitée
                
                adjacent_group = f'location_{lat_zone + lat_offset}_{lng_zone + lng_offset}'
                
                # Calculer la distance pour les zones adjacentes
                geo_service = GeolocationService()
                center_lat = (lat_zone + lat_offset) / 100.0
                center_lng = (lng_zone + lng_offset) / 100.0
                
                distance = geo_service.calculate_distance(
                    (float(lieu.latitude), float(lieu.longitude)),
                    (center_lat, center_lng)
                )
                
                if distance and distance <= 15:  # 15km de rayon
                    send_to_websocket(
                        adjacent_group,
                        'proximity_event_notification',
                        {
                            'event_data': event_data,
                            'distance': distance
                        }
                    )
    
    except Exception as e:
        logger.error(f"Erreur notifications basées localisation: {e}")


@receiver(post_delete, sender=Evenement)
def evenement_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'un événement"""
    logger.info(f"Événement supprimé: {instance.nom}")
    
    # Créer des données minimales pour l'événement supprimé
    event_data = {
        'id': str(instance.id),
        'nom': instance.nom,
        'date_debut': instance.date_debut.isoformat(),
        'lieu_nom': instance.lieu.nom if instance.lieu else 'Inconnu'
    }
    
    send_to_websocket(
        'events_notifications',
        'event_cancelled_notification',
        {'event_data': event_data}
    )


@receiver(post_save, sender=Lieu)
def lieu_created_or_updated(sender, instance, created, **kwargs):
    """Signal déclenché lors de la création/modification d'un lieu"""
    
    if created:
        logger.info(f"Nouveau lieu créé: {instance.nom}")
        
        # Sérialiser le lieu
        place_data = LieuListSerializer(instance).data
        
        # Notification globale
        send_to_websocket(
            'events_notifications',
            'new_place_notification',
            {'place_data': place_data}
        )
        
        # Notification par catégorie
        if instance.categorie:
            category_group = f"category_{instance.categorie.lower().replace(' ', '_')}"
            send_to_websocket(
                category_group,
                'new_place_notification',
                {'place_data': place_data}
            )


@receiver(post_save, sender=AvisEvenement)
def avis_evenement_created(sender, instance, created, **kwargs):
    """Signal pour les nouveaux avis d'événements"""
    
    if created:
        logger.info(f"Nouvel avis pour événement: {instance.evenement.nom}")
        
        # Notifier le propriétaire de l'événement
        organisateur = instance.evenement.organisateur
        send_to_websocket(
            f'user_{organisateur.id}',
            'personal_notification',
            {
                'notification_data': {
                    'type': 'new_review',
                    'message': f"Nouvel avis sur votre événement '{instance.evenement.nom}'",
                    'rating': instance.note,
                    'event_id': str(instance.evenement.id)
                }
            }
        )


@receiver(post_save, sender=AvisLieu)
def avis_lieu_created(sender, instance, created, **kwargs):
    """Signal pour les nouveaux avis de lieux"""
    
    if created:
        logger.info(f"Nouvel avis pour lieu: {instance.lieu.nom}")
        
        # Notifier le propriétaire du lieu
        proprietaire = instance.lieu.proprietaire
        send_to_websocket(
            f'user_{proprietaire.id}',
            'personal_notification',
            {
                'notification_data': {
                    'type': 'new_place_review',
                    'message': f"Nouvel avis sur votre lieu '{instance.lieu.nom}'",
                    'rating': instance.note,
                    'place_id': str(instance.lieu.id)
                }
            }
        )


# Tâche périodique pour les rappels d'événements
def send_event_reminders():
    """
    Fonction à appeler périodiquement (avec Celery ou cron)
    pour envoyer des rappels d'événements
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Événements qui commencent dans 1 heure
    one_hour_later = timezone.now() + timedelta(hours=1)
    upcoming_events = Evenement.objects.filter(
        date_debut__lte=one_hour_later,
        date_debut__gt=timezone.now()
    ).select_related('organisateur', 'lieu')
    
    for event in upcoming_events:
        event_data = EvenementListSerializer(event).data
        
        # Rappel à l'organisateur
        send_to_websocket(
            f'user_{event.organisateur.id}',
            'event_reminder',
            {
                'event_data': event_data,
                'reminder_time': '1 heure'
            }
        )
        
        # Rappel global (pour les utilisateurs intéressés par la zone)
        send_location_based_notifications(event, event_data, 'reminder')


# Signal personnalisé pour les événements à venir
from django.dispatch import Signal

event_starting_soon = Signal()

@receiver(event_starting_soon)
def handle_event_starting_soon(sender, event, **kwargs):
    """Gérer les événements qui commencent bientôt"""
    event_data = EvenementListSerializer(event).data
    
    send_to_websocket(
        'events_notifications',
        'event_starting_soon',
        {
            'event_data': event_data,
            'message': f"L'événement '{event.nom}' commence dans peu de temps"
        }
    )