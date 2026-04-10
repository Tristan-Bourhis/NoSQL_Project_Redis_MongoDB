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


.PHONY: generate

generate:
	$(UV) generate_data.py


.PHONY: help

help:
	@echo "Cibles disponibles :"
	@echo "  up          - Demarrer Redis + MongoDB (Docker)"
	@echo "  down        - Arreter les conteneurs"
	@echo "  restart     - Redemarrer les conteneurs"
	@echo "  logs        - Voir les logs Docker"
	@echo "  generate    - Generer et charger les donnees initiales"
