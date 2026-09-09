ARG PHP_VERSION=8.4

FROM docker.io/library/php:$PHP_VERSION-apache

# https://hub.docker.com/_/php
# https://github.com/NathanVaughn/webtrees-docker/issues/160
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

ENV WEBTREES_HOME="/var/www/webtrees"
WORKDIR $WEBTREES_HOME

# install pre-reqs
# postgresql-client provides pg_isready
# mariadb-client provides mysqladmin
# vim-tiny provides vi
RUN apt-get update \
 && apt-get install -y \
    curl \
    libmagickwand-dev \
    libpq-dev \
    libzip-dev \
    postgresql-client \
    mariadb-client \
    patch \
    python3 \
    unzip \
    vim-tiny \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# install php extensions
# opcache is only built where the base image does not already provide it
# (statically built since PHP 8.5, cannot be built as a shared module there)
RUN pecl install imagick \
 && docker-php-ext-enable imagick \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j"$(nproc)" pdo pdo_mysql pdo_pgsql zip intl gd exif \
 && if ! php -m | grep -qi opcache; then docker-php-ext-install opcache; fi

# remove old apt stuff
RUN apt-get purge gcc g++ make -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/tmp/* /etc/apache2/sites-enabled/000-*.conf

ARG WEBTREES_VERSION
RUN curl -s -L https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -o webtrees.zip \
 && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip \
 && rm $WEBTREES_HOME/*.md \
# directory for custom modules/themes, see https://webtrees.net/download/modules
 && mkdir -p $WEBTREES_HOME/modules_v4

# Disable version update prompt. Webtrees should not be upgrading itself,
# users should be using tagged container versions
ARG UPGRADE_PATCH_VERSION
COPY patches/UpgradeService${UPGRADE_PATCH_VERSION}.patch /UpgradeService.patch
RUN patch app/Services/UpgradeService.php /UpgradeService.patch \
 && rm /UpgradeService.patch \
# Delete file that caused email issues
# https://www.webtrees.net/index.php/fr/forum/help-for-2-0/36616-email-error-after-update-to-2-0-21#89985
# https://github.com/NathanVaughn/webtrees-docker/issues/88
 && rm vendor/egulias/email-validator/src/Validation/MessageIDValidation.php

# enable apache modules and switch to unprivileged ports so Apache can
# run as www-data (no root needed to bind 8080/8443)
RUN a2enmod rewrite && a2enmod ssl && rm -rf /var/www/html \
 && sed -ri 's/^(\s*)Listen 80$/\1Listen 8080/; s/^(\s*)Listen 443$/\1Listen 8443/' /etc/apache2/ports.conf

# copy apache/php configs
RUN mkdir -p /bak/webtrees/data/ \
 && cp $WEBTREES_HOME/data/.htaccess /bak/webtrees/data/.htaccess
COPY .htaccess ./
COPY apache/ /etc/apache2/sites-available/

# entrypoint
COPY docker-entrypoint.py /

# healthcheck
COPY docker-healthcheck.sh /
RUN chmod +x /docker-healthcheck.sh

# convenience alias for interactive shells (make shell-app)
RUN echo "alias ll='ls -lAF'" >> /etc/bash.bashrc

# hand every path the entrypoint writes at runtime over to www-data
# (apache site configs + php.ini are edited by docker-entrypoint.py,
# a2ensite/a2dissite write state markers to /var/lib/apache2,
# data/ and modules_v4/ are volumes and inherit this ownership)
RUN chown -R www-data:www-data \
    /etc/apache2/sites-available \
    /etc/apache2/sites-enabled \
    /var/lib/apache2 \
    "$PHP_INI_DIR/php.ini" \
    "$WEBTREES_HOME/data" \
    "$WEBTREES_HOME/modules_v4" \
# lock the root account (no password login, no shell) and strip all
# setuid/setgid bits so nothing inside the container can escalate to root
 && usermod --lock --shell /usr/sbin/nologin root \
 && find / -xdev -perm /6000 -type f -exec chmod a-s {} +

# final Docker config
EXPOSE 8080 8443
VOLUME ["$WEBTREES_HOME/data"]

HEALTHCHECK CMD /docker-healthcheck.sh

# run everything as www-data - no process in this container runs as root
USER www-data
ENTRYPOINT ["python3", "/docker-entrypoint.py"]
