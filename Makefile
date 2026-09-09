# Convenience targets for the webtrees stack.
# All targets use rootless Podman; override with: make ENGINE=docker <target>

ENGINE ?= podman
COMPOSE = $(ENGINE) compose

.DEFAULT_GOAL := help

.PHONY: help init certs up down restart ps logs logs-db build backup restore \
        upgrade update autostart autostart-remove shell-app shell-db check prune \
        module modules

help: ## show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

init: ## create .env from the template (first-time setup)
	@test -f .env && echo ".env already exists" || (cp .env.example .env && \
		echo "Created .env - now edit it and set the passwords!")

certs: ## generate self-signed TLS certs: make certs [HOST=name-or-ip]
	./scripts/gen-certs.sh $(HOST)

up: ## build (if needed) and start the stack
	$(COMPOSE) up -d --build

down: ## stop and remove the containers (volumes are kept)
	$(COMPOSE) down

restart: ## restart the stack
	$(COMPOSE) restart

ps: ## show container status
	$(COMPOSE) ps

logs: ## follow webtrees logs
	$(COMPOSE) logs -f app

logs-db: ## follow database logs
	$(COMPOSE) logs -f db

build: ## (re)build the webtrees image
	$(COMPOSE) build app

backup: ## create a backup in ./backups/<timestamp>/
	./scripts/backup.sh

restore: ## restore a backup: make restore BACKUP=backups/<timestamp>
	@test -n "$(BACKUP)" || (echo "usage: make restore BACKUP=backups/<timestamp>"; exit 1)
	./scripts/restore.sh "$(BACKUP)"

module: ## install a custom module/theme: make module SRC=<url-or-archive>
	@test -n "$(SRC)" || (echo "usage: make module SRC=<url-or-zip/tar.gz-file>"; exit 1)
	./scripts/install-module.sh "$(SRC)"

modules: ## list installed custom modules
	./scripts/install-module.sh --list

upgrade: ## rebuild + restart; new version: make upgrade VERSION=2.2.7
	./scripts/upgrade.sh $(VERSION)

update: upgrade ## alias for upgrade

autostart: ## install systemd user unit (start on boot, Linux only)
	./scripts/install-autostart.sh

autostart-remove: ## remove the systemd user unit
	./scripts/install-autostart.sh --remove

shell-app: ## open a shell in the webtrees container
	$(ENGINE) exec -it webtrees-app bash

shell-db: ## open a mariadb prompt in the database container
	$(ENGINE) exec -it webtrees-db sh -c 'mariadb -uroot -p"$$MARIADB_ROOT_PASSWORD" "$$MARIADB_DATABASE"'

check: ## validate compose file and script syntax
	$(COMPOSE) config --quiet && echo "compose config: OK"
	@for f in scripts/*.sh; do bash -n $$f && echo "$$f: OK"; done

prune: ## remove dangling images left over from rebuilds
	$(ENGINE) image prune -f
