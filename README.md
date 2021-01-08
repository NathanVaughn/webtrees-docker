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
[docker-compose.yml](https://github.com/NathanVaughn/webtrees-docker/blob/dev/docker-compose.yml).

### Environment Variables - NEW!

There are many environment variables available to help automatically configure
the container. For any environment variable you do not define,
the default value will be used.

| Environment Variable               | Required | Default    | Notes                                                                                                                                                                                                           |
| ---------------------------------- | -------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PRETTY_URLS`                      | No       | None       | Setting this to any value will enable [pretty URLs](https://webtrees.net/faq/urls/). This can be toggled at any time.                                                                                           |
| `HTTPS` or `SSL`                   | No       | None       | Setting this to any value will enable HTTPS. In this case, you _must_ mount a directory containing `webtrees.crt` and `webtrees.key` certificates to the directory `/certs/`. For example: `-v ~/certs:/certs/` |
| `HTTPS_REDIRECT` or `SSL_REDIRECT` | No       | None       | Setting this to any value will enable a _permanent_ 301 redirect to HTTPS . Leaving this off will allow webtrees to be accessed over HTTP, but not automatically redirected to HTTPS.                           |
| `LANG`                             | No       | `en-us`    | webtrees localization setting. This takes a locale code. Examples: <https://wpastra.com/docs/complete-list-wordpress-locale-codes/>                                                                             |
| `BASE_URL`                         | Yes      | None       | Base URL of the installation, with protocol. This needs to be in the form of `http://webtrees.example.com`                                                                                                      |
| `DB_TYPE`                          | No       | `mysql`    | Database server type. See [below](#database) for valid values.                                                                                                                                                  |
| `DB_HOST`                          | Yes      | None       | Database server host.                                                                                                                                                                                           |
| `DB_PORT`                          | No       | `3306`     | Database server port.                                                                                                                                                                                           |
| `DB_USER` or `MYSQL_USER`          | No       | `webtrees` | Database server username.                                                                                                                                                                                       |
| `DB_PASS` or `MYSQL_PASSWORD`      | Yes      | None       | Database server password.                                                                                                                                                                                       |
| `DB_NAME` or `MYSQL_DATABASE`      | No       | `webtrees` | Database name.                                                                                                                                                                                                  |
| `DB_PREFIX`                        | No       | `wt_`      | Prefix to give all tables in the database. Set this to a value of `""` to have no table prefix.                                                                                                                 |
| `WT_USER`                          | Yes      | None       | First admin account username. Note, this is only used the first time the container is run, and the database is initialized.                                                                                     |
| `WT_NAME`                          | Yes      | None       | First admin account full name. Note, this is only used the first time the container is run, and the database is initialized.                                                                                    |
| `WT_PASS`                          | Yes      | None       | First admin account password. Note, this is only used the first time the container is run, and the database is initialized.                                                                                     |
| `WT_EMAIL`                         | Yes      | None       | First admin account email. Note, this is only used the first time the container is run, and the database is initialized.                                                                                        |

If you don't want the container to be configured automatically
(if you're migrating from an existing webtrees installation for example), simply leave
the database (`DB_`) and webtrees (`WT_`) variables blank, and you can complete the
[setup wizard](https://i.imgur.com/rw70cgW.png) like normal.

### Database

webtrees [recommends](https://webtrees.net/install/requirements/)
a MySQL (or compatible equivalent) database.
You will need a separate container for this.

-   [MariaDB](https://hub.docker.com/_/mariadb)
-   [MySQL](https://hub.docker.com/_/mysql)

PostgreSQL and SQLite are additionally both supported by webtrees and this image, but
are not recommended. This image does not support Microsoft SQL Server, in order
to support multiple architectures. See issue:
[microsoft/msphpsql#441](https://github.com/microsoft/msphpsql/issues/441#issuecomment-310237200)

#### SQLite Values

If you want to use a SQLite database, set the following values:

-   `DB_TYPE` to `sqlite`
-   `DB_NAME` to `desiredfilename`. Do not include any extension.

#### PostgreSQL Values

If you want to use a PostreSQL database, set the following values:

-   `DB_TYPE` to `pgsql`
-   `DB_PORT` to `5432`

All other values are just like a MySQL database.

### Volumes

The image mounts:

-   `/var/www/webtrees/data/`
-   `/var/www/webtrees/media/`

If you want to add custom [themes or modules](https://webtrees.net/download/modules),
you can also mount the `/var/www/webtrees/modules_v4/` directory.

Example `docker-compose`:

```yml
volumes:
  - app_data:/var/www/webtrees/data/
  - app_media:/var/www/webtrees/media/
  - app_themes:/var/www/webtrees/modules_v4/
---
volumes:
  app_data:
    driver: local
  app_media:
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

> **🚨⚠ WARNING ⚠🚨**
> If you use the 2.X.X or **beta** versions of webtrees,
> you will **_NOT_** be able to use the
> 1.X.X version again. The database schema between these versions are
> very different, and this is a one-way operation.

### Specific Versions

Each stable, legacy, beta, and alpha release version of webtrees
produces a version-tagged build of the Docker container.

Example:

```yml
image: nathanvaughn/webtrees:1.7.15
```

### Latest

Currently, the tags `latest` and `latest-beta` are available for the latest
stable and beta versions of webtrees, respectively.

Example:

```yml
image: nathanvaughn/webtrees:latest-beta
```

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
update wt_site_setting set setting_value='https://example.com/login.php' where setting_name='LOGIN_URL';
update wt_site_setting set setting_value='http://example.com/' where setting_name='SERVER_URL';
quit;
```

For more info, see [this](https://webtrees.net/admin/proxy/).

## Inspiration

The Dockerfile is heavily based off
[solidnerd/docker-bookstack](https://github.com/solidnerd/docker-bookstack).
