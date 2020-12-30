#!/bin/bash

echo "Setting folder permissions for uploads"
chown -R www-data:www-data data && chmod -R 775 data
chown -R www-data:www-data media && chmod -R 775 media

CONFIG_FILE="data/config.ini.php"

if [ -f "$CONFIG_FILE" ]
then
    # remove exisitng line from file
    sed -i '/^rewrite_urls/d' "$CONFIG_FILE"

    # test for zero length
    if [[ -z "${PRETTY_URLS}" ]]
    then
        echo "Removing pretty URLs"
        echo 'rewrite_urls="0"' >> $CONFIG_FILE
    else
        echo "Adding pretty URLs"
        echo 'rewrite_urls="1"' >> $CONFIG_FILE
    fi
else
    echo "Config file not found, please setup webtrees."
fi

# test both for zero length
if [[ -z "${HTTPS}" && -z "${SSL}" ]]
then
    echo "Removing HTTPS support"
    a2dissite webtrees-ssl
    a2dissite webtrees-redir
    a2ensite  webtrees
else
    # test both for zero length
    if [[ -z "${HTTPS_REDIRECT}" && -z "${SSL_REDIRECT}" ]]
    then
        echo "Adding HTTPS, removing HTTPS redirect"
        a2dissite webtrees-redir
        a2ensite  webtrees
        a2ensite  webtrees-ssl
    else
        echo "Adding HTTPS, adding HTTPS redirect"
        a2dissite webtrees
        a2ensite  webtrees-redir
        a2ensite  webtrees-ssl
    fi
fi

exec apache2-foreground