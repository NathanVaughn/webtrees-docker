FROM php:7.3.13-apache-stretch

ENV WEBTREES_VERSION=2.0.0-beta.5
ENV WEBTREES_HOME="/var/www/webtrees"

RUN apt-get update && apt-get install -y git wget unzip zlib1g-dev libfreetype6-dev libjpeg62-turbo-dev libmcrypt-dev libpng-dev libldap2-dev libtidy-dev libzip-dev --no-install-recommends\
   && docker-php-ext-install pdo pdo_mysql zip \
   && docker-php-ext-configure gd --with-freetype-dir=usr/include/ --with-jpeg-dir=/usr/include/ \
   && docker-php-ext-install gd \
   && wget https://github.com/fisharebest/webtrees/releases/download/${WEBTREES_VERSION}/webtrees-${WEBTREES_VERSION}.zip -O webtrees.zip \
   && unzip -q webtrees.zip -d /var/www/ && rm webtrees.zip  \
   && chown -R www-data:www-data $WEBTREES_HOME \
   && apt-get -y autoremove \
   && apt-get clean \
   && rm -rf /var/lib/apt/lists/* /var/tmp/* /etc/apache2/sites-enabled/000-*.conf

COPY php.ini /usr/local/etc/php/php.ini
COPY webtrees.conf /etc/apache2/sites-enabled/webtrees.conf
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
