# Docker Image for [webtrees](https://webtrees.net/)


[![](https://img.shields.io/docker/cloud/build/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/v/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/image-size/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/docker/pulls/nathanvaughn/webtrees)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://img.shields.io/github/license/nathanvaughn/webtrees-docker)](https://github.com/NathanVaughn/webtrees-docker)

This is a basic, up-to-date Docker image for
[webtrees](https://github.com/fisharebest/webtrees) served over HTTP,
designed to be put behind a reverse proxy such as CloudFlare.

## Usage

### Quickstart

An example `docker-compose.yml` file is provided for reference.

You can launch the example with `docker-compose up -d`.

Once you start the container, you can visit
[http://localhost:1000/](http://localhost:1000/) and begin the
[setup wizard](https://wiki.webtrees.net/en/Installation#Server_configuration_check).

### Network

The image exposes port 80.

Example `docker-compose`:

```yml
  ports:
    - 80:80
```

### Volumes

The image mounts:
  - `/var/www/webtrees/data/`
  - `/var/www/webtrees/media/`

If you want to add custom themes, you can also mount the
`/var/www/webtrees/themes/` directory.

Example `docker-compose`:

```yml
  volumes:
    - app_data:/var/www/webtrees/data/
    - app_media:/var/www/webtrees/media/
    - app_themes:/var/www/webtrees/themes/

...

volumes:
  app_data:
    driver: local
  app_media:
    driver: local
  app_themes:
    driver: local
```

### Database

webtrees [recommends](https://webtrees.net/install/requirements/)
a MySQL (or compatible equivalent) database.
You will need a separate container for this.

- [MariaDB](https://hub.docker.com/_/mariadb)
- [MySQL](https://hub.docker.com/_/mysql)

PostgreSQL and SQLite are additionally both supported by webtrees and this image, but
are not recommended. This image currently does not support Microsoft SQL Server.

### Pretty URLS

If you would like to enable [pretty URLs](https://webtrees.net/faq/urls/),
set the environment variable `PRETTY_URLS` to any value.
This can be toggled at any time.

Example `docker-compose`:

```yml
environment:
  PRETTY_URLS: "1"
```

***Note:*** This will only take into effect the *second* time you start the container.
This cannot be enabled in webtrees until you have completed the setup process.
Therefore, start the container for the first time, complete the setup, then restart
the container.

## Tags

> **🚨⚠ WARNING ⚠🚨**
If you use the 2.X.X or **beta** versions of webtrees,
you will ***NOT*** be able to use the
1.X.X version again. The database schema between these versions are
very different, and this is a one-way operation.

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
over HTTPS, but using this HTTP container, you might need to make the following
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
