FROM docker.io/library/php:7.4-apache

ARG BUILD_DATE
ARG VCS_REF

ENV WEBTREES_HOME="/var/www/webtrees"
WORKDIR $WEBTREES_HOME

# install pre-reqs
RUN apt-get update
RUN apt-get install -y \
    curl \
    libmagickwand-dev \
    libpq-dev \
    libzip-dev \
    mariadb-client \
    patch \
    python3 \
    unzip \
    --no-install-recommends
# install php extensions
RUN pecl install imagick \
 && docker-php-ext-enable imagick \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j$(nproc) pdo pdo_mysql pdo_pgsql zip intl gd exif
# remove old apt stuff
RUN apt-get purge gcc g++ make -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/tmp/* /etc/apache2/sites-enabled/000-*.conf /var/lib/apt/lists/*

# install webtrees and disable version update prompt
ENV WEBTREES_VERSION=2.0.19
RUN curl -s -L https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -o webtrees.zip \
 && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip \
 && chown -R www-data:www-data ./ \
 && perl -0777 -i -pe "s/private\s+function\s+fetchLatestVersion[\S\s]+?{[\S\s]+?{[\S\s]+?{[\S\s]+?{[\S\s]+?}[\S\s]+?}[\S\s]+?}[\S\s]+?}[\S\s]+?}/private function fetchLatestVersion(): string { return Site::getPreference('LATEST_WT_VERSION'); }/" app/Services/UpgradeService.php

# enable apache modules
RUN a2enmod rewrite && a2enmod ssl && rm -rf /var/www/html

# copy apache/php configs
COPY php.ini /usr/local/etc/php/php.ini
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
