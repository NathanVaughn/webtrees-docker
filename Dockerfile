ARG PHP_VERSION=8.1

FROM docker.io/library/php:$PHP_VERSION-apache

ENV WEBTREES_HOME="/var/www/webtrees"
WORKDIR $WEBTREES_HOME

# install pre-reqs
RUN apt-get update \
 && apt-get install -y \
    curl \
    libmagickwand-dev \
    libpq-dev \
    libzip-dev \
    mariadb-client \
    patch \
    python3 \
    unzip \
    --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*
# install php extensions
RUN pecl install imagick \
 && docker-php-ext-enable imagick \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j"$(nproc)" pdo pdo_mysql pdo_pgsql zip intl gd exif
# remove old apt stuff
RUN apt-get purge gcc g++ make -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/tmp/* /etc/apache2/sites-enabled/000-*.conf

ARG WEBTREES_VERSION
COPY UpgradeService.patch /UpgradeService.patch
RUN curl -s -L https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -o webtrees.zip \
 && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip
RUN chown -R www-data:www-data $WEBTREES_HOME \
# Disable version update prompt. Webtrees should not be upgrading itself,
# users should be using tagged container versions
 && patch app/Services/UpgradeService.php /UpgradeService.patch \
 && rm /UpgradeService.patch \
# Delete file that caused email issues
# https://www.webtrees.net/index.php/fr/forum/help-for-2-0/36616-email-error-after-update-to-2-0-21#89985
# https://github.com/NathanVaughn/webtrees-docker/issues/88
 && rm vendor/egulias/email-validator/src/Validation/MessageIDValidation.php

# enable apache modules
RUN a2enmod rewrite && a2enmod ssl && rm -rf /var/www/html

# copy apache/php configs
COPY .htaccess ./
COPY apache/ /etc/apache2/sites-available/

# entrypoint
COPY docker-entrypoint.py /

# healthcheck
COPY docker-healthcheck.sh /
RUN chmod +x /docker-healthcheck.sh

# final Docker config
EXPOSE 80 443
VOLUME ["$WEBTREES_HOME/data", "$WEBTREES_HOME/media"]

HEALTHCHECK CMD /docker-healthcheck.sh
ENTRYPOINT ["python3", "/docker-entrypoint.py"]
