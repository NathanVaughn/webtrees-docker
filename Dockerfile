FROM php:8.0.2-apache

ENV WEBTREES_VERSION=2.0.11
ENV WEBTREES_HOME="/var/www/webtrees"

RUN apt-get update && apt-get install -y git curl locales locales-all mariadb-client g++ unzip zlib1g-dev libfreetype6-dev libjpeg62-turbo-dev libpng-dev libmcrypt-dev libzip-dev libicu-dev libpq-dev libmagickwand-dev --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN pecl install imagick \
 && docker-php-ext-enable imagick \
 && docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j$(nproc) pdo pdo_mysql pdo_pgsql zip intl gd exif
RUN curl -s -L https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -o webtrees.zip \
 && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip \
 && chown -R www-data:www-data $WEBTREES_HOME
RUN apt-get purge g++ make zip unzip -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/tmp/* /etc/apache2/sites-enabled/000-*.conf

# for perl
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

COPY php.ini /usr/local/etc/php/php.ini
COPY .htaccess $WEBTREES_HOME

COPY webtrees.conf /etc/apache2/sites-available/webtrees.conf
COPY webtrees-redir.conf /etc/apache2/sites-available/webtrees-redir.conf
COPY webtrees-ssl.conf /etc/apache2/sites-available/webtrees-ssl.conf

RUN a2enmod rewrite && a2enmod ssl

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

WORKDIR $WEBTREES_HOME

EXPOSE 80
EXPOSE 443

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
