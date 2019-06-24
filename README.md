# Docker Image for [Webtrees](https://www.webtrees.net/index.php/en/)

[![](https://img.shields.io/docker/cloud/build/nathanvaughn/webtrees.svg?style=popout)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/image/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/version/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/license/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)

This is an up-to-date Docker image for webtrees served over HTTP, designed to be put behind a reverse proxy such as Cloudflare.

## Usage

### Quickstart

An example `docker-compose.yml` file is provided for reference.

You can launch the example with `docker-compose up -d`.

Once you start the container, you can visit http://localhost:1000/setup.php and begin the setup wizard.

### Network

The image exposes port 80.

### Volumes

The image mounts:
  - `/var/www/webtrees/data/`
  - `/var/www/webtrees/media/`

### MySQL

Webtrees requires a MySQL database. You will need a separate container for this.

## Inspiration
This is heavily based off [solidnerd/docker-bookstack](https://github.com/solidnerd/docker-bookstack).
