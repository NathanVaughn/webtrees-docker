# Docker Image for [webtrees](https://webtrees.net/)

[![](https://github.com/NathanVaughn/webtrees-docker/workflows/Check%20and%20Push%20Updates/badge.svg)](https://github.com/NathanVaughn/webtrees-docker)
[![](https://img.shields.io/docker/v/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/image-size/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/pulls/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/github/license/nathanvaughn/webtrees-docker)](https://github.com/NathanVaughn/webtrees-docker)

This is a multi-architecture, up-to-date, Docker image for
[webtrees](https://github.com/fisharebest/webtrees) served over HTTP or HTTPS.
This can be put behind a reverse proxy such as CloudFlare or Traefik, or
run standalone.

## Usage

### Quickstart

If you want to jump right in, take a look at the provided
[docker-compose.yml](https://github.com/NathanVaughn/webtrees-docker/blob/master/docker-compose.yml).

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

PostgreSQL and SQLite are additionally both supported by webtrees and this image, but
are not recommended. This image does not support Microsoft SQL Server, in order
to support multiple architectures. See issue:
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

The image mounts:

- `/var/www/webtrees/data/`

(media is stored in the `media` subfolder)

If you want to add custom [themes or modules](https://webtrees.net/download/modules),
you can also mount the `/var/www/webtrees/modules_v4/` directory.

Example `docker-compose`:

```yml
volumes:
  - app_data:/var/www/webtrees/data/
  - app_themes:/var/www/webtrees/modules_v4/
---
volumes:
  app_data:
    driver: local
  app_themes:
    driver: local
```

See the link above for information about v1.7 webtrees.

To install a custom theme or module, the process is generally as follows:

```bash
docker exec -it webtrees_app_1 bash   # connect to the running container
cd /var/www/webtrees/modules_v4/      # move into the modules directory
curl -L <download url> -o <filename>  # download the file

# if module is a .tar.gz file
tar -xf <filename.tar.gz>             # extract the tar archive https://xkcd.com/1168/
rm <filename.tar.gz>                  # remove the tar archive

# if module is a .zip file
apt update && apt install unzip       # install the unzip package
unzip <filename.zip>                  # extract the zip file
rm <filename.zip>                     # remove the zip file

exit                                  # disconnect from the container
```

### Network

The image exposes port 80 and 443.

Example `docker-compose`:

```yml
ports:
  - 80:80
  - 443:443
```

If you have the HTTPS redirect enabled, you still need to expose port 80.
If you're not using HTTPS at all, you don't need to expose port 443.

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
webtrees versions. This means a human does not vette every release. While
I try to stay on top of things, sometimes breaking issues do occur. If you
have any, please feel free to fill out an
[issue](https://github.com/NathanVaughn/webtrees-docker/issues).

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

This image is available from 3 different registries. Choose whichever you want:

- [docker.io/nathanvaughn/webtrees](https://hub.docker.com/r/nathanvaughn/webtrees)
- [ghcr.io/nathanvaughn/webtrees](https://github.com/users/nathanvaughn/packages/container/package/webtrees)
- [cr.nathanv.app/library/webtrees](https://cr.nathanv.app/harbor/projects/1/repositories/webtrees) (experimental)
