# Étape PostgreSQL

Le moteur et Streamlit utilisent actuellement SQLite. Cette étape charge une projection relationnelle d’un snapshot dans PostgreSQL 17 ou ultérieur. Elle ne bascule pas automatiquement le tableau de bord vers PostgreSQL.

Le schéma conserve les trois tables maîtres typées, les clés de version, les correspondances sources, la provenance et les relations. Le snapshot complet est aussi conservé en JSONB avec les données brutes et les événements appliqués. Les clés étrangères empêchent les correspondances orphelines ; voir la [documentation PostgreSQL sur les contraintes](https://www.postgresql.org/docs/17/ddl-constraints.html).

Préparer l’export :

```powershell
.\.venv\Scripts\python.exe scripts\export_postgres.py
```

Avec Docker Desktop démarré, choisir un mot de passe local et le fournir dans la session, puis :

```powershell
$env:MDM_POSTGRES_PASSWORD = Read-Host 'Mot de passe PostgreSQL de démonstration'
docker compose up -d --wait
docker compose cp sql/schema.sql postgres:/tmp/schema.sql
docker compose cp dist/import_mdm.sql postgres:/tmp/import_mdm.sql
docker compose exec -T postgres psql -U mdm_demo -d hospital_mdm -v ON_ERROR_STOP=1 -f /tmp/schema.sql
docker compose exec -T postgres psql -U mdm_demo -d hospital_mdm -v ON_ERROR_STOP=1 -f /tmp/import_mdm.sql
docker compose exec -T postgres psql -U mdm_demo -d hospital_mdm -c 'SELECT domain, count(*) FROM mdm.master_entity GROUP BY domain;'
```

Le port exposé sur l’ordinateur est 5433, limité à 127.0.0.1. Le volume Docker conserve les données après arrêt. `docker compose stop` arrête le service sans effacer le volume. L’export est transactionnel et refuse une seconde importation de la même version grâce à la clé primaire : créer une nouvelle version avant un nouvel import.

Sans Docker, exécuter les deux fichiers dans une base PostgreSQL locale au moyen de `psql -v ON_ERROR_STOP=1 -f <fichier>`. Aucun mot de passe n’est inclus dans le dépôt.

L’authentification applicative, les rôles SQL, les migrations incrémentales et l’historisation normalisée des décisions constituent l’étape suivante. La projection SQL est préparée pour la démonstration, pas annoncée comme une intégration serveur de production.
