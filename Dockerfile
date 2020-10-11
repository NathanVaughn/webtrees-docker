FROM php:7.4-apache

ENV WEBTREES_VERSION=2.0.9
ENV WEBTREES_HOME="/var/www/webtrees"

RUN apt-get update && apt-get install -y git wget g++ unzip zip zlib1g-dev libfreetype6-dev libjpeg62-turbo-dev libpng-dev libmcrypt-dev libzip-dev libicu-dev libpq-dev libmagickwand-dev --no-install-recommends
RUN pecl install imagick \
 && docker-php-ext-enable imagick \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j$(nproc) pdo pdo_mysql pdo_pgsql zip intl gd exif
RUN wget -q https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -O webtrees.zip \
 && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip \
 && chown -R www-data:www-data $WEBTREES_HOME
RUN apt-get purge g++ make zip unzip -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /var/tmp/* /etc/apache2/sites-enabled/000-*.conf

COPY php.ini /usr/local/etc/php/php.ini
COPY webtrees.conf /etc/apache2/sites-enabled/webtrees.conf
COPY .htaccess $WEBTREES_HOME
RUN a2enmod rewrite

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

WORKDIR $WEBTREES_HOME

EXPOSE 80

VOLUME ["$WEBTREES_HOME/data", "$WEBTREES_HOME/media"]

ENTRYPOINT ["/docker-entrypoint.sh"]

ARG BUILD_DATE
ARG VCS_REF
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
      org.label-schema.vcs-type="Git"
