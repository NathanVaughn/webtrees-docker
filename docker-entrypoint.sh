#!/bin/bash

echo "Setting folder permissions for uploads"
chown -R www-data:www-data data && chmod -R 775 data
chown -R www-data:www-data media && chmod -R 775 media

CONFIG_FILE="data/config.ini.php"
PREFIX="[NV_INIT]"

auto_wizard () {
    echo "$PREFIX Attempting to automate setup wizard."

    # defaults
    lang="${LANG:-en-US}"
    dbtype="${DB_TYPE:-mysql}"
    dbport="${DB_PORT:-3306}"
    dbuser="${DB_USER:-${MYSQL_USER:-webtrees}}"
    dbname="${DB_NAME:-${MYSQL_DATABASE:-webtrees}}"
    tblpfx="${DB_PREFIX:-wt_}"

    # required
    dbhost="${DB_HOST}"
    dbpass="${DB_PASS:-$MYSQL_PASSWORD}"
    baseurl="${BASE_URL}"
    wtname="${WT_NAME}"
    wtuser="${WT_USER}"
    wtpass="${WT_PASS}"
    wtemail="${WT_EMAIL}"

    if [ -f "$CONFIG_FILE" ]
    then
        echo "$PREFIX Config file found."

        if [[ -z "$dbhost" || -z "$dbport" || -z "$dbuser" || -z "$dbpass" || -z "$dbname" || -z "$baseurl" || -z "$tblpfx" ]]
        then
            echo "$PREFIX Not all variables required for config file update."
            return 0
        fi

        echo "$PREFIX Updating config file."

        sed -i '/^dbhost/d' "$CONFIG_FILE" && echo "dbhost=\"$dbhost\"" >> $CONFIG_FILE
        sed -i '/^dbport/d' "$CONFIG_FILE" && echo "dbport=\"$dbport\"" >> $CONFIG_FILE
        sed -i '/^dbuser/d' "$CONFIG_FILE" && echo "dbuser=\"$dbuser\"" >> $CONFIG_FILE
        sed -i '/^dbpass/d' "$CONFIG_FILE" && echo "dbpass=\"$dbpass\"" >> $CONFIG_FILE
        sed -i '/^dbname/d' "$CONFIG_FILE" && echo "dbname=\"$dbname\"" >> $CONFIG_FILE
        sed -i '/^tblpfx/d' "$CONFIG_FILE" && echo "tblpfx=\"$tblpfx\"" >> $CONFIG_FILE
        sed -i '/^base_url/d' "$CONFIG_FILE" && echo "base_url=\"$baseurl\"" >> $CONFIG_FILE

    else
        echo "$PREFIX Config file NOT found."

        if [[ -z "$dbhost" || -z "$dbpass" || -z "$baseurl" || -z "$wtname" || -z "$wtuser" || -z "$wtpass" || -z "$wtemail" ]]
        then
            echo "$PREFIX Not all variables required for setup wizard present."
            return 0
        fi

        echo "$PREFIX Automating setup wizard."

        service apache2 start

        curl -X POST \
        -F "lang=$lang" \
        -F "dbtype=$dbtype" \
        -F "dbhost=$dbhost" \
        -F "dbport=$dbport" \
        -F "dbuser=$dbuser" \
        -F "dbpass=$dbpass" \
        -F "dbname=$dbname" \
        -F "tblpfx=$tblpfx" \
        -F "baseurl=$baseurl" \
        -F "wtname=$wtname" \
        -F "wtuser=$wtuser" \
        -F "wtpass=$wtpass" \
        -F "wtemail=$wtemail" \
        -F "step=6" \
        http://127.0.0.1:80

        service apache2 stop
    fi
}

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

pretty_urls () {
    echo "$PREFIX Attempting to set pretty URLs status."

    if [ -f "$CONFIG_FILE" ]
    then
        echo "$PREFIX Config file found."

        # remove exisiting line from file
        sed -i '/^rewrite_urls/d' "$CONFIG_FILE"

        if [[ -z "${PRETTY_URLS}" ]]
        then
            echo "$PREFIX Removing pretty URLs."
            echo 'rewrite_urls="0"' >> $CONFIG_FILE
        else
            echo "$PREFIX Adding pretty URLs."
            echo 'rewrite_urls="1"' >> $CONFIG_FILE
        fi
    else
        echo "$PREFIX Config file NOT found, please setup webtrees."
    fi
}

auto_wizard
pretty_urls

echo "$PREFIX Starting Apache."

exec apache2-foreground