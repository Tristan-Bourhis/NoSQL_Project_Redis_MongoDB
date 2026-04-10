# Systeme de livraison - Redis & MongoDB

Projet NoSQL utilisant Redis (temps reel) et MongoDB (historique/analyses) pour gerer un systeme de livraison. Interface web avec FastAPI + React.

## Prerequis

- **Make** (outil de build)
- Docker et Docker Compose
- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets Python)
- Node.js 20+ et npm (pour le dev frontend local)

### Installation de Make

Linux (Debian/Ubuntu) :

```bash
sudo apt update && sudo apt install make
```

macOS (via Xcode Command Line Tools) :

```bash
xcode-select --install
```

Windows (via Chocolatey) :

```bash
choco install make
```

Verifier l'installation :

```bash
make --version
```

## Mise en route

### Option 1 : Docker (recommande)

Lance les 4 services (Redis, MongoDB, API, Frontend) :

```bash
make up
make generate
```

Acces :
- Frontend : http://localhost:3000
- API Swagger : http://localhost:8000/docs

Pour rebuilder apres modification du code :

```bash
docker compose up -d --build api frontend
```

### Option 2 : Dev local (hot reload)

Lancer Redis + MongoDB via Docker, puis l'API et le frontend en local :

```bash
docker compose up -d redis mongodb
make generate
make api    # terminal 1 - API sur port 8000
make front  # terminal 2 - Frontend sur port 5173
```

Acces :
- Frontend : http://localhost:5173
- API Swagger : http://localhost:8000/docs

## Interface web

Dashboard unique avec 4 onglets :

- **Commandes** : liste par statut, assignation d'un livreur, completion
- **Livreurs** : tableau avec rating, regions, filtre par region, top 5
- **Geo** : carte Leaflet avec lieux/livreurs, recherche par rayon, livreurs proches
- **Analytics** : performance par region, top livreurs par revenu (MongoDB)

Stack : React, TypeScript, shadcn/ui, TanStack Query, Leaflet, Vite, Nginx.

## CLI Redis

```bash
make assign           # Affecter c1 a d3
make report           # Commandes en attente vs assignees
make complete         # Simuler fin de livraison c1/d3
make dashboard        # Etat global du systeme
make demo             # Scenario complet
make drivers-by-region  # Livreurs operant a Paris
make cache-refresh    # Rafraichir le cache (TTL 30s)
make cache-show       # Afficher le cache
```

## CLI MongoDB

```bash
make mongo            # Executer tous les travaux
```

Sous-commandes individuelles :

```bash
uv run -m delivery_system.mongo_cli import
uv run -m delivery_system.mongo_cli history --driver d1
uv run -m delivery_system.mongo_cli regions
uv run -m delivery_system.mongo_cli top --limit 5
uv run -m delivery_system.mongo_cli indexes
```

## Geo-spatial

```bash
make geo              # Executer tous les travaux geo
```

## Commandes Make

| Commande | Description |
|----------|-------------|
| `make up` | Demarrer tous les services (Docker) |
| `make down` | Arreter les conteneurs |
| `make restart` | Redemarrer les conteneurs |
| `make logs` | Voir les logs Docker |
| `make generate` | Charger les donnees initiales |
| `make api` | Lancer l'API FastAPI (port 8000) |
| `make front` | Lancer le frontend Vite (port 5173) |
| `make demo` | Scenario complet Redis |
| `make mongo` | Tous les travaux MongoDB |
| `make geo` | Travaux geo-spatiaux |
| `make drivers-by-region` | Livreurs multi-regions |
| `make cache-refresh` | Rafraichir le cache (TTL 30s) |
| `make cache-show` | Afficher le cache |

## Structure du projet

```text
.
|-- api/
|   `-- main.py              # API FastAPI (tous les endpoints)
|-- delivery_system/
|   |-- __init__.py
|   |-- cli.py               # CLI Redis
|   |-- service.py            # Operations Redis transactionnelles
|   |-- mongo_cli.py          # CLI MongoDB
|   `-- mongo_service.py      # Requetes et agregations MongoDB
|-- frontend/
|   |-- src/
|   |   |-- components/       # Dashboard, onglets, composants UI
|   |   |-- hooks/            # TanStack Query hooks
|   |   `-- lib/              # API client, utilitaires
|   |-- Dockerfile            # Build Node + Nginx
|   `-- nginx.conf            # Reverse proxy /api -> backend
|-- docker-compose.yml        # 4 services : redis, mongodb, api, frontend
|-- Dockerfile                # Image API Python
|-- config.py                 # Connexions Redis/MongoDB (env vars)
|-- generate_data.py          # Generation de donnees
|-- geo.py                    # Commandes geo-spatiales Redis
|-- sync.py                   # Synchronisation Redis -> MongoDB
|-- Makefile
`-- requirements.txt
```
