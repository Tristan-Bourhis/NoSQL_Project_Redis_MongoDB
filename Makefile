UV = uv run --with redis --with pymongo --with faker


.PHONY: up down restart logs

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down && docker compose up -d

logs:
	docker compose logs -f


.PHONY: generate assign report complete dashboard demo mongo drivers-by-region cache-refresh cache-show geo

generate:
	$(UV) generate_data.py

assign:
	$(UV) -m delivery_system.cli assign --order c1 --driver d3

report:
	$(UV) -m delivery_system.cli report

complete:
	$(UV) -m delivery_system.cli complete --order c1 --driver d3

dashboard:
	$(UV) -m delivery_system.cli dashboard

demo:
	$(UV) -m delivery_system.cli demo --order c1 --driver d3

mongo:
	$(UV) -m delivery_system.mongo_cli all

drivers-by-region:
	$(UV) -m delivery_system.cli drivers-by-region --region Paris

cache-refresh:
	$(UV) -m delivery_system.cli cache-refresh

cache-show:
	$(UV) -m delivery_system.cli cache-show

geo:
	$(UV) geo.py


.PHONY: help

help:
	@echo "Cibles disponibles :"
	@echo "  up          - Demarrer Redis + MongoDB (Docker)"
	@echo "  down        - Arreter les conteneurs"
	@echo "  restart     - Redemarrer les conteneurs"
	@echo "  logs        - Voir les logs Docker"
	@echo "  generate    - Generer et charger les donnees initiales"
	@echo "  assign      - Affecter c1 a d3 de maniere atomique (transaction Redis)"
	@echo "  report      - Afficher commandes en attente vs assignees + meilleur rating"
	@echo "  complete    - Simuler la fin de livraison c1 par d3"
	@echo "  dashboard   - Afficher le dashboard global temps reel"
	@echo "  demo        - Executer le scenario complet (report + simulation + dashboard)"
	@echo "  mongo       - Lancer les requetes MongoDB (Partie 2)"
	@echo "  drivers-by-region - Livreurs operant a Paris (Partie 3)"
	@echo "  cache-refresh     - Rafraichir le cache Redis (TTL 30s)"
	@echo "  cache-show        - Afficher le contenu du cache"
	@echo "  geo               - Lancer les travaux geo-spatiaux (Partie 4)"
