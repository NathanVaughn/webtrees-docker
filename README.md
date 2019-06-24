# Docker Image for [Webtrees](https://www.webtrees.net/index.php/en/)

[![](https://img.shields.io/docker/cloud/build/nathanvaughn/webtrees.svg?style=popout)](https://hub.docker.com/r/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/image/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/version/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)
[![](https://images.microbadger.com/badges/license/nathanvaughn/webtrees.svg)](https://microbadger.com/images/nathanvaughn/webtrees)

## Usage

Once you start with the container, you can visit http://ipaddress:port/setup.php and begin the setup wizard.

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
