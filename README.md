# Docker Image for [webtrees](https://www.webtrees.net/index.php/en/)

[![](https://img.shields.io/docker/cloud/build/nathanvaughn/webtrees.svg?style=popout)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/image/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/version/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/license/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)

This is an up-to-date Docker image for
[webtrees](https://github.com/fisharebest/webtrees) served over HTTP,
designed to be put behind a reverse proxy such as Cloudflare.

## Usage

### Quickstart

An example `docker-compose.yml` file is provided for reference.

You can launch the example with `docker-compose up -d`.

Once you start the container, you can visit
[http://localhost:1000/setup.php](http://localhost:1000/setup.php) and begin the
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

### MySQL

webtrees requires a MySQL (or compatible equivalent) database.
You will need a separate container for this.

- [MariaDB](https://hub.docker.com/_/mariadb)
- [MySQL](https://hub.docker.com/_/mysql)

## Tags

> **🚨⚠ WARNING ⚠🚨**
If you use the **beta** version of webtrees, you will ***NOT*** be able to use the
stable version again. The database schema between the stable and beta versions are
very different, and this is a one-way operation. Make a full backup before choosing
to try the beta version of webtrees so that you can roll back if needed.

### Specific Versions
Each stable, beta, and alpha release version of webtrees
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

## Reverse Proxy Issues

webtrees does not like running behind a reverse proxy, and depending on your setup,
you may need to adjust some database values manually.

For example, if you are accessing webtrees via a reverse proxy serving content
over HTTPS, but using this HTTP container, you would need to make the following
changes in your database:

```sql
mysql -u webtrees -p

use webtrees;
update wt_site_setting set setting_value='https://example.com/login.php' where setting_name='LOGIN_URL';
update wt_site_setting set setting_value='http://example.com/' where setting_name='SERVER_URL';
quit;
```

## Inspiration
The Dockerfile is heavily based off
[solidnerd/docker-bookstack](https://github.com/solidnerd/docker-bookstack).
