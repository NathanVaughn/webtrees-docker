#!/bin/bash

echo "Setting folder permissions for uploads"
chown -R www-data:www-data data && chmod -R 775 data
chown -R www-data:www-data media && chmod -R 775 media

CONFIG_FILE="/var/www/webtrees/data/config.ini.php"

if [ -f "$CONFIG_FILE" ]
then
    # remove exisitng line from file
    sed -i '/^rewrite_urls/d' "$CONFIG_FILE"

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

exec apache2-foreground