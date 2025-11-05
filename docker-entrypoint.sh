#!/bin/bash
set -e

echo "🚀 Démarrage de l'application Lomé Explorer..."

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente de PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "postgres" -d "lome_explorer_db" -c '\q'; do
  >&2 echo "PostgreSQL indisponible - attente..."
  sleep 1
done

echo "✅ PostgreSQL est prêt!"

# Attendre que Redis soit prêt
echo "⏳ Attente de Redis..."
until redis-cli -h redis ping; do
  >&2 echo "Redis indisponible - attente..."
  sleep 1
done

echo "✅ Redis est prêt!"

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate --noinput

# Créer un superutilisateur si nécessaire
echo "👤 Création du superutilisateur..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@lome.com', 'admin123')
    print('✅ Superutilisateur créé: admin/admin123')
else:
    print('ℹ️  Superutilisateur existe déjà')
END

# Collecter les fichiers statiques
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Charger des données de test (optionnel)
# echo "📊 Chargement des données de test..."
# python manage.py loaddata fixtures/initial_data.json

echo "✅ Configuration terminée!"
echo "🌐 L'application démarre sur le port 8000..."

# Exécuter la commande passée au conteneur
exec "$@"