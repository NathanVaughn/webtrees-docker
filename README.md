# Docker Image for [webtrees](https://webtrees.net/)

[![](https://github.com/NathanVaughn/webtrees-docker/workflows/Check%20and%20Push%20Updates/badge.svg)](https://github.com/NathanVaughn/webtrees-docker)
[![](https://img.shields.io/docker/v/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/image-size/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/pulls/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/github/license/rkl110/webtrees-docker)](https://github.com/rkl110/webtrees-docker)

This is a multi-architecture, up-to-date, Docker image for
[webtrees](https://github.com/fisharebest/webtrees) served over HTTP or HTTPS.
This can be put behind a reverse proxy such as CloudFlare or Traefik, or
run standalone.

This repository ([rkl110/webtrees-docker](https://github.com/rkl110/webtrees-docker))
is a fork of
[NathanVaughn/webtrees-docker](https://github.com/NathanVaughn/webtrees-docker),
adapted for a rootless Podman deployment (see the Quickstart below). The
prebuilt Docker images referenced in this README are published by the
original project.

## Usage

### Quickstart (rootless Podman)

The provided [docker-compose.yml](docker-compose.yml) is designed to run
rootless with Podman (it works with Docker too). The webtrees image is
built locally from this repository ([docker/Dockerfile](docker/Dockerfile)),
the MariaDB image is pulled. All settings and secrets come from a `.env`
file:

```bash
# 1. create your configuration
cp .env.example .env
# edit .env: set the passwords (DB_PASS, MARIADB_ROOT_PASSWORD, WT_PASS),
# the admin account and BASE_URL

# 2. build the webtrees image and start the stack
podman compose up -d --build
```

webtrees is then available at <http://localhost:8080> (and, if HTTPS is
enabled, at <https://localhost:8443>). Both ports are unprivileged so no
root permissions are required. All application data (media, GEDCOM files,
config), custom modules/themes and the database live in the named volumes
`webtrees_app_data`, `webtrees_app_modules` and `webtrees_db_data`.

Both containers run entirely **without root**: the webtrees image sets
`USER www-data` (Apache listens on the unprivileged ports 8080/8443
inside the container), the database runs as the `mysql` user, all
capabilities are dropped and `no-new-privileges` is set. In the webtrees
image the root account is additionally locked and all setuid/setgid
binaries are removed, so no process can escalate to root inside the
container.

Requirements: Podman 4.7+ with `podman compose` (or `podman-compose`).

#### Start on boot (Debian/Linux server, rootless)

Rootless Podman has no daemon, so a restart policy alone does not survive
a reboot (`restart: always` only covers container crashes while the system
is running). For a rootless user on a systemd-based server (e.g. Debian),
install the provided systemd user unit once:

```bash
./scripts/install-autostart.sh
```

This enables lingering for your user (services run without an active
login), installs `~/.config/systemd/user/webtrees.service` — which runs
`podman compose up -d` on boot — and enables it. The stack can then also
be managed with `systemctl --user start|stop|status webtrees`.
Use `--print` to inspect the generated unit and `--remove` to uninstall.

Alternative: Podman's native [Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
units are the canonical systemd integration, but they replace compose as
the orchestrator entirely. Since this project is compose-based, the
wrapper unit keeps `docker-compose.yml` the single source of truth.

#### HTTPS with self-signed certificates

```bash
make certs                      # hostname taken from BASE_URL in .env
# or: make certs HOST=server.example.com
```

This writes `certs/webtrees.crt` and `certs/webtrees.key` (gitignored),
which are mounted read-only into the container. Then set in `.env`:

```bash
HTTPS=1
HTTPS_REDIRECT=1                # optional: force HTTPS
BASE_URL=https://<host>:8443
```

and recreate the stack (`podman compose down && podman compose up -d` —
a plain `restart` does not pick up `.env` changes). webtrees is then
served on port 8443. Browsers will warn about the self-signed
certificate; import `certs/webtrees.crt` as trusted or use a reverse
proxy with a real certificate for public installations. Bring-your-own
certificates work too — just place them at the same paths.

Note for your own certificates: Apache runs as `www-data` (uid 33), which
with rootless Podman maps to a subuid of your host user — a key file with
`600` permissions owned by your host user is therefore **not readable**
inside the container (`mod_ssl: Permission denied`). Make the key readable
(`chmod 644 certs/webtrees.key`; `make certs` does this automatically), or
keep it private with
`podman unshare chown 33:33 certs/webtrees.key`.

#### Behind a reverse proxy

For public installations, terminate TLS at a reverse proxy with a real
certificate and keep webtrees on plain HTTP behind it
(see also <https://webtrees.net/admin/proxy/>). In `.env`:

```bash
BASE_URL=https://family.example.com   # the public URL
HTTPS=0                               # TLS terminates at the proxy
BIND_ADDRESS=127.0.0.1                # app only reachable via the proxy
TRUSTED_PROXIES=10.0.2.0/24           # proxy address as seen by the container
```

`TRUSTED_PROXIES` (comma-separated IPs/CIDR ranges) tells webtrees which
`X-Forwarded-For` headers to trust, so rate limiting and logs see real
client IPs. With rootless Podman, connections arrive from an internal
gateway address — check the client IP shown in
*Control panel → Server information* and trust that. Only trust proxies
when direct access to the app port is blocked (`BIND_ADDRESS=127.0.0.1`),
otherwise clients could spoof their IP. If your proxy sends the client IP
in a custom header, set `TRUSTED_HEADERS` (e.g. `cf-connecting-ip` for
Cloudflare).

Example [Caddy](https://caddyserver.com/) config on the same host —
Caddy gets Let's Encrypt certificates automatically:

```text
family.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

After changing `.env`, recreate the stack:
`podman compose down && podman compose up -d`.

#### Updates and upgrades

The webtrees version is pinned via `WEBTREES_VERSION` in `.env`:

```bash
./scripts/upgrade.sh          # rebuild the current version (fresh base image) and restart
./scripts/upgrade.sh 2.2.7    # switch to a different webtrees version
```

The script creates a backup first (skip with `--no-backup`), updates
`.env`, pulls the MariaDB image, rebuilds the webtrees image and
recreates the containers. webtrees migrates its database schema
automatically when a newer version starts. When changing the version,
check [dev/versions.json](dev/versions.json) for the matching
`PHP_VERSION` and `UPGRADE_PATCH_VERSION` build arguments in `.env`.

#### Backup and restore

```bash
./scripts/backup.sh                            # backup to ./backups/<timestamp>/
./scripts/restore.sh backups/20260714-120000   # restore a backup
```

A backup contains a consistent SQL dump of the database (`db.sql.gz`),
a tar export of the app data volume (`app_data.tar.gz`) and a copy of the
`.env` file (`env.backup`). Backups are taken while the stack is running;
a restore stops the stack, recreates both volumes and starts it again.
Since the database is restored from a SQL dump, backups also survive
MariaDB major version changes. Store the `backups/` directory somewhere
safe (it is gitignored and contains your credentials).

### Environment Variables

There are many environment variables available to help automatically configure
the container. For any environment variable you do not define,
the default value will be used.

> **🚨 WARNING 🚨**
> These environment variables will be visible in the webtrees control panel
> under "Server information". Either lock down the control panel
> to administrators, or use the webtrees setup wizard.

| Environment Variable                                                       | Required | Default               | Notes                                                                                                                                                                                                             |
| -------------------------------------------------------------------------- | -------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PRETTY_URLS`                                                              | No       | `False`               | Setting this to any truthy value (`True`, `1`, `yes`) will enable [pretty URLs](https://webtrees.net/faq/urls/). This can be toggled at any time, however you must go through initial setup at least once first.  |
| `HTTPS` or `SSL`                                                           | No       | `False`               | Setting this to any truthy value (`True`, `1`, `yes`) will enable HTTPS. If `True`, you must also fill out `SSL_CERT_FILE` and `SSL_CERT_KEY_FILE`                                                                |
| `HTTPS_REDIRECT` or `SSL_REDIRECT`                                         | No       | `False`               | Setting this to any truthy value (`True`, `1`, `yes`) will enable a _permanent_ 301 redirect to HTTPS . Leaving this off will allow webtrees to be accessed over HTTP, but not automatically redirected to HTTPS. |
| `SSL_CERT_FILE`                                                            | No       | `/certs/webtrees.crt` | Certificate file to use for HTTPS. Can either be absolute, or relative to `/var/www/webtrees/data/`.                                                                                                              |
| `SSL_CERT_KEY_FILE`                                                        | No       | `/certs/webtrees.key` | Certificate key file to use for HTTPS. Can either be absolute, or relative to `/var/www/webtrees/data/`.                                                                                                          |
| `LANG`                                                                     | Yes      | `en-us`               | webtrees localization setting. This takes a locale code. List: <https://github.com/fisharebest/webtrees/tree/main/resources/lang/>                                                                               |
| `BASE_URL`                                                                 | Yes      | None                  | Base URL of the installation, with protocol. This needs to be in the form of `http://webtrees.example.com`                                                                                                        |
| `DB_TYPE`                                                                  | Yes      | `mysql`               | Database server type. See [below](#database) for valid values.                                                                                                                                                    |
| `DB_HOST`                                                                  | Yes      | None                  | Database server host.                                                                                                                                                                                             |
| `DB_PORT`                                                                  | Yes      | `3306`                | Database server port.                                                                                                                                                                                             |
| `DB_USER` or `MYSQL_USER` or `MARIADB_USER` or `POSTGRES_USER`             | Yes      | `webtrees`            | Database server username.                                                                                                                                                                                         |
| `DB_PASS` or `MYSQL_PASSWORD` or `MARIADB_PASSWORD` or `POSTGRES_PASSWORD` | Yes      | None                  | Database server password.                                                                                                                                                                                         |
| `DB_NAME` or `MYSQL_DATABASE` or `MARIADB_DATABASE` or `POSTGRES_DB`       | Yes      | `webtrees`            | Database name.                                                                                                                                                                                                    |
| `DB_PREFIX`                                                                | Yes      | `wt_`                 | Prefix to give all tables in the database. Set this to a value of `""` to have no table prefix.                                                                                                                   |
| `DB_KEY`                                                                   | No       | None                  | Key file used to verify the MySQL server. Only use with the `mysql` database driver. Relative to the `/var/www/webtrees/data/` directory.                                                                         |
| `DB_CERT`                                                                  | No       | None                  | Certificate file used to verify the MySQL server. Only use with the `mysql` database driver. Relative to the `/var/www/webtrees/data/` directory.                                                                 |
| `DB_CA`                                                                    | No       | None                  | Certificate authority file used to verify the MySQL server. Only use with the `mysql` database driver. Relative to the `/var/www/webtrees/data/` directory.                                                       |
| `DB_VERIFY`                                                                | No       | `False`               | Whether to verify the MySQL server. Only use with the `mysql` database driver. If `True`, you must also fill out `DB_KEY`, `DB_CERT`, and `DB_CA`.                                                                |
| `WT_USER`                                                                  | Yes      | None                  | First admin account username. Note, this is only used the first time the container is run, and the database is initialized.                                                                                       |
| `WT_NAME`                                                                  | Yes      | None                  | First admin account full name. Note, this is only used the first time the container is run, and the database is initialized.                                                                                      |
| `WT_PASS`                                                                  | Yes      | None                  | First admin account password. Note, this is only used the first time the container is run, and the database is initialized.                                                                                       |
| `WT_EMAIL`                                                                 | Yes      | None                  | First admin account email. Note, this is only used the first time the container is run, and the database is initialized.                                                                                          |
| `PHP_MEMORY_LIMIT`                                                         | No       | `1024M`               | PHP memory limit. See the [PHP documentation](https://www.php.net/manual/en/ini.core.php#ini.memory-limit)                                                                                                        |
| `PHP_MAX_EXECUTION_TIME`                                                   | No       | `90`                  | PHP max execution time for a request in seconds. See the [PHP documentation](https://www.php.net/manual/en/info.configuration.php#ini.max-execution-time)                                                         |
| `PHP_POST_MAX_SIZE`                                                        | No       | `50M`                 | PHP POST request max size. See the [PHP documentation](https://www.php.net/manual/en/ini.core.php#ini.post-max-size)                                                                                              |
| `PHP_UPLOAD_MAX_FILE_SIZE`                                                 | No       | `50M`                 | PHP max uploaded file size. See the [PHP documentation](https://www.php.net/manual/en/ini.core.php#ini.upload-max-filesize)                                                                                       |

Note: the upstream `PUID`/`PGID` variables are not supported by this fork.
The container always runs as `www-data` (33) and never as root, so it cannot
change UIDs at runtime. With rootless Podman, use `podman run --userns` /
`--uidmap` options (or the compose `userns_mode` key) if you need a
different host-side mapping.

Additionally, you can add `_FILE` to the end of any environment variable name,
and instead that will read the value in from the given filename.
For example, setting `DB_PASS_FILE=/run/secrets/my_db_secret` will read the contents
of that file into `DB_PASS`.

If you don't want the container to be configured automatically
(if you're migrating from an existing webtrees installation for example), simply leave
the database (`DB_`) and webtrees (`WT_`) variables blank, and you can complete the
[setup wizard](https://i.imgur.com/rw70cgW.png) like normal.

### Database

webtrees [recommends](https://webtrees.net/install/requirements/)
a MySQL (or compatible equivalent) database.
You will need a separate container for this.

- [MariaDB](https://hub.docker.com/_/mariadb)
- [MySQL](https://hub.docker.com/_/mysql)

PostgreSQL (`pgsql`) and SQLite (`sqlite`) are additionally both supported by
webtrees and this image, but are [not recommended](https://github.com/fisharebest/webtrees/issues/5099#issuecomment-2581440755).
This image does not support Microsoft SQL Server, in order to support multiple
architectures. See issue:
[microsoft/msphpsql#441](https://github.com/microsoft/msphpsql/issues/441#issuecomment-310237200)

#### SQLite Values

If you want to use a SQLite database, set the following values:

- `DB_TYPE` to `sqlite`
- `DB_NAME` to `desiredfilename`. Do not include any extension.

#### PostgreSQL Values

If you want to use a PostreSQL database, set the following values:

- `DB_TYPE` to `pgsql`
- `DB_PORT` to `5432`

All other values are just like a MySQL database.

### Volumes

The provided [docker-compose.yml](docker-compose.yml) mounts:

- `/var/www/webtrees/data/` (volume `webtrees_app_data`) — application
  data; media is stored in the `media` subfolder
- `/var/www/webtrees/modules_v4/` (volume `webtrees_app_modules`) —
  custom [themes and modules](https://webtrees.net/download/modules)

Both volumes are included in `./scripts/backup.sh` / `restore.sh`.

### Custom modules and themes

Custom modules/themes live in `/var/www/webtrees/modules_v4/`
(one subdirectory per module) and survive rebuilds and upgrades via the
`webtrees_app_modules` volume. The easiest way to install one is the
provided script, which accepts a download URL or a local archive
(`.zip`, `.tar.gz` or `.tar.bz2`):

```bash
./scripts/install-module.sh https://example.com/some-module.zip
# or: make module SRC=https://example.com/some-module.zip

./scripts/install-module.sh --list            # list installed modules
./scripts/install-module.sh --remove <name>   # remove a module
```

Afterwards, enable the module in webtrees under
_Control panel → Modules_.

Alternatively, install manually inside the running container:

```bash
podman exec -it webtrees-app bash     # connect to the running container
cd /var/www/webtrees/modules_v4/      # move into the modules directory
curl -L <download url> -o <filename>  # download the file

# if module is a .tar.gz file
tar -xf <filename.tar.gz>             # extract the tar archive https://xkcd.com/1168/
rm <filename.tar.gz>                  # remove the tar archive

# if module is a .zip file
unzip <filename.zip>                  # extract the zip file
rm <filename.zip>                     # remove the zip file

exit                                  # disconnect from the container
```

(No `chown` needed: the container runs as `www-data`, so all extracted
files already belong to the right user.)

### Network

The image exposes the unprivileged ports 8080 (HTTP) and 8443 (HTTPS) -
Apache runs as `www-data` and therefore cannot bind ports below 1024.

Example `docker-compose`:

```yml
ports:
  - 8080:8080
  - 8443:8443
```

If you have the HTTPS redirect enabled, you still need to expose port 8080.
If you're not using HTTPS at all, you don't need to expose port 8443.

### ImageMagick

`ImageMagick` is included in this image to speed up
[thumbnail creation](https://webtrees.net/faq/thumbnails/).
webtrees will automatically prefer it over `gd` with no configuration.

## Tags

### Specific Versions

Each stable, legacy, beta, and alpha release version of webtrees
produces a version-tagged build of the Docker container.

Example:

```yml
image: ghcr.io/nathanvaughn/webtrees:2.1.2
```

### Latest

Currently, the tags `latest`, `latest-alpha`, `latest-beta` and `latest-legacy`
are available for the latest stable, alpha, beta and legacy versions of webtrees,
respectively.

Example:

```yml
image: ghcr.io/nathanvaughn/webtrees:latest
```

> **Note**
> Legacy versions of webtrees are no longer supported.

## Issues

New releases of the Dockerfile are automatically generated from upstream
webtrees versions. This means a human does not vette every release, so
sometimes breaking issues do occur. For problems with this fork (Podman
setup, compose file, scripts), please open an
[issue in this repository](https://github.com/rkl110/webtrees-docker/issues).
For general problems with the image itself, check the
[upstream issues](https://github.com/NathanVaughn/webtrees-docker/issues).

## Reverse Proxy Issues

webtrees does not like running behind a reverse proxy, and depending on your setup,
you may need to adjust some database values manually.

For example, if you are accessing webtrees via a reverse proxy serving content
over HTTPS, but using this container with HTTP, you _might_ need to make the following
changes in your database:

```sql
mysql -u webtrees -p

use webtrees;
update wt_site_setting set setting_value='https://example.com/login' where setting_name='LOGIN_URL';
update wt_site_setting set setting_value='https://example.com/' where setting_name='SERVER_URL';
quit;
```

For more info, see [this](https://webtrees.net/admin/proxy/).

## Registry

This image is available from 2 different registries. Choose whichever you want:

- [docker.io/nathanvaughn/webtrees](https://hub.docker.com/r/nathanvaughn/webtrees)
- [ghcr.io/nathanvaughn/webtrees](https://github.com/users/nathanvaughn/packages/container/package/webtrees)
