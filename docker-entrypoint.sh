#!/bin/bash
set -e

echo "🚀 Démarrage de l'application Lomé Explorer..."

# Variables d'environnement avec valeurs par défaut
DB_HOST="${DB_HOST:-db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-lome_explorer_db}"
DB_PASSWORD="${DB_PASSWORD:-Doubidjinadey}"

# Export du mot de passe pour psql
export PGPASSWORD="$DB_PASSWORD"

# Fonction pour tester PostgreSQL
check_postgres() {
    psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null
}

# Fonction pour tester Redis
check_redis() {
    redis-cli -h redis ping 2>/dev/null | grep -q PONG
}

# Attendre PostgreSQL
echo "⏳ Attente de PostgreSQL ($DB_HOST:5432)..."
MAX_TRIES=30
TRIES=0
until check_postgres; do
    TRIES=$((TRIES + 1))
    if [ $TRIES -ge $MAX_TRIES ]; then
        echo "❌ PostgreSQL n'a pas démarré après $MAX_TRIES tentatives"
        exit 1
    fi
    echo "PostgreSQL indisponible - tentative $TRIES/$MAX_TRIES..."
    sleep 2
done
echo "✅ PostgreSQL est prêt!"


# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p /app/logs /app/staticfiles /app/media

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate --noinput

# Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
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
python manage.py collectstatic --noinput --clear

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Configuration terminée!"
echo "🌐 L'application démarre sur http://0.0.0.0:8000"
echo "🔌 WebSocket disponible sur ws://0.0.0.0:8000/ws/"
echo "👤 Admin: admin / admin123"
echo "═══════════════════════════════════════════════"
echo ""

# Exécuter la commande passée au conteneur
exec "$@"