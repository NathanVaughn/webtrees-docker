FROM php:7.3.8-apache-stretch

ENV WEBTREES_VERSION=1.7.14 \
    WEBTREES_HOME="/var/www/webtrees"

RUN apt-get update && apt-get install -y git wget zlib1g-dev libfreetype6-dev libjpeg62-turbo-dev libmcrypt-dev libpng-dev wget libldap2-dev libtidy-dev\
   && docker-php-ext-install pdo pdo_mysql \
   && docker-php-ext-configure gd --with-freetype-dir=usr/include/ --with-jpeg-dir=/usr/include/ \
   && docker-php-ext-install gd \
   && wget https://github.com/fisharebest/webtrees/archive/${WEBTREES_VERSION}.tar.gz -O webtrees.tar.gz \
   && tar -xf webtrees.tar.gz && mv webtrees-${WEBTREES_VERSION} ${WEBTREES_HOME} && rm webtrees.tar.gz  \
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
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.docker.dockerfile="/Dockerfile" \
      org.label-schema.license="MIT" \
      org.label-schema.name="webtrees" \
      org.label-schema.vendor="nathanvaughn" \
      org.label-schema.url="https://github.com/nathanvaughn/webtrees-docker" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/nathanvaughn/webtrees-docker.git" \
      org.label-schema.vcs-type="Git"