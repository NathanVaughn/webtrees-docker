FROM docker.io/library/php:7.4-apache

ARG BUILD_DATE
ARG VCS_REF

ENV WEBTREES_VERSION=2.1.0-alpha.1
ENV WEBTREES_HOME="/var/www/webtrees"

RUN apt-get update
# break this installs into smaller, 100MB chunks
RUN apt-get install -y \
      curl \
      g++ \
      git \
      locales \
      locales-all \
      mariadb-client \
      unzip \
      --no-install-recommends
RUN apt-get install -y \
      libfreetype6-dev \
      libicu-dev \
      libjpeg62-turbo-dev \
      libmagickwand-dev \
      libmcrypt-dev \
      libpng-dev \
      libpq-dev \
      libzip-dev \
      zlib1g-dev \
      --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*
RUN pecl install imagick \
 && docker-php-ext-enable imagick \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j$(nproc) pdo pdo_mysql pdo_pgsql zip intl gd exif
RUN curl -s -L https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -o webtrees.zip \
 && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip \
 && chown -R www-data:www-data $WEBTREES_HOME \
 && perl -0777 -i -pe 's/public\s+function\s+isUpgradeAvailable[\S\s]+?{[\S\s]+?}/public function isUpgradeAvailable(){ return false; }/' $WEBTREES_HOME/app/Services/UpgradeService.php
RUN apt-get purge g++ make zip unzip -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/tmp/* /etc/apache2/sites-enabled/000-*.conf

# for perl
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# copy some apache/php configs
COPY php.ini /usr/local/etc/php/php.ini
COPY .htaccess $WEBTREES_HOME
COPY apache/ /etc/apache2/sites-available/

RUN a2enmod rewrite && a2enmod ssl

# entrypoint
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# healthcheck
COPY docker-healthcheck.sh /
RUN chmod +x /docker-healthcheck.sh

WORKDIR $WEBTREES_HOME

EXPOSE 80
EXPOSE 443

VOLUME ["$WEBTREES_HOME/data", "$WEBTREES_HOME/media"]

HEALTHCHECK CMD /docker-healthcheck.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

LABEL org.label-schema.schema-version="1.0" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="nathanvaughn/webtrees" \
      org.label-schema.description="Docker image for webtrees" \
      org.label-schema.license="MIT" \
      org.label-schema.url="https://github.com/nathanvaughn/webtrees-docker" \
      org.label-schema.vendor="nathanvaughn" \
      org.label-schema.version=$WEBTREES_VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/nathanvaughn/webtrees-docker.git" \
      org.label-schema.vcs-type="Git" \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.title="nathanvaughn/webtrees" \
      org.opencontainers.image.description="Docker image for webtrees" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://github.com/nathanvaughn/webtrees-docker" \
      org.opencontainers.image.authors="Nathan Vaughn" \
      org.opencontainers.image.vendor="nathanvaughn" \
      org.opencontainers.image.version=$WEBTREES_VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.source="https://github.com/nathanvaughn/webtrees-docker.git"
