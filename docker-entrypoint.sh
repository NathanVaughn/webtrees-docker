#!/bin/bash

echo "Setting folder permissions for uploads"
chown -R www-data:www-data data && chmod -R 775 data
chown -R www-data:www-data media && chmod -R 775 media

CONFIG_FILE="data/config.ini.php"
PREFIX="[NV_INIT]"

auto_wizard () {
    # automatically try to complete the setup wizard
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

    # test if config file exists
    if [ -f "$CONFIG_FILE" ]
    then
        echo "$PREFIX Config file found."

        # make sure all of the variables for the config file are present
        if [[ -z "$dbhost" || -z "$dbport" || -z "$dbuser" || -z "$dbpass" || -z "$dbname" || -z "$baseurl" ]]
        then
            echo "$PREFIX Not all variables required for config file update."
            return 0
        fi

        echo "$PREFIX Updating config file."

        # remove the line with sed, then write new content
        sed -i '/^dbhost/d' "$CONFIG_FILE" && echo "dbhost=\"$dbhost\"" >> $CONFIG_FILE
        sed -i '/^dbport/d' "$CONFIG_FILE" && echo "dbport=\"$dbport\"" >> $CONFIG_FILE
        sed -i '/^dbuser/d' "$CONFIG_FILE" && echo "dbuser=\"$dbuser\"" >> $CONFIG_FILE
        sed -i '/^dbpass/d' "$CONFIG_FILE" && echo "dbpass=\"$dbpass\"" >> $CONFIG_FILE
        sed -i '/^dbname/d' "$CONFIG_FILE" && echo "dbname=\"$dbname\"" >> $CONFIG_FILE
        sed -i '/^tblpfx/d' "$CONFIG_FILE" && echo "tblpfx=\"$tblpfx\"" >> $CONFIG_FILE
        sed -i '/^base_url/d' "$CONFIG_FILE" && echo "base_url=\"$baseurl\"" >> $CONFIG_FILE

    else
        echo "$PREFIX Config file NOT found."

        # make sure all of the variables needed for the setup wizard are present
        if [[ -z "$lang" || -z "$dbtype" || -z "$dbhost" || -z "$dbport" || -z "$dbuser" || -z "$dbpass" || -z "$dbname" || -z "$baseurl" || -z "$wtname" || -z "$wtuser" || -z "$wtpass" || -z "$wtemail" ]]
        then
            echo "$PREFIX Not all variables required for setup wizard present."
            return 0
        fi

        echo "$PREFIX Automating setup wizard."

        # start apache in the background quickly to send the request
        service apache2 start

        # set us up to a known HTTP state
        a2dissite webtrees-ssl
        a2dissite webtrees-redir
        a2ensite  webtrees
        service apache2 reload

        # wait until database is ready
        if [ "$dbtype" = "mysql" ]; then
            while ! mysqladmin ping -h"$dbhost" --silent; do
                echo "$PREFIX Waiting for MySQL server to be ready."
                sleep 1
            done
        else
            echo "$PREFIX Waiting 10 seconds arbitrarily for database server to be ready."
            sleep 10
        fi

        # POST the data and follow redirects and ignore SSL errors, if HTTPS is enabled and forced
        curl -L -k -X POST \
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

        # stop apache so that we can start it as a foreground process
        service apache2 stop
    fi
}

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

https () {
    echo "$PREFIX Attempting to set HTTPS status."

    if [[ -z "${HTTPS}" && -z "${SSL}" ]]
    then
        echo "$PREFIX Removing HTTPS support"
        a2dissite webtrees-ssl
        a2dissite webtrees-redir
        a2ensite  webtrees
    else
        if [[ -z "${HTTPS_REDIRECT}" && -z "${SSL_REDIRECT}" ]]
        then
            echo "$PREFIX Adding HTTPS, removing HTTPS redirect"
            a2dissite webtrees-redir
            a2ensite  webtrees
            a2ensite  webtrees-ssl
        else
            echo "$PREFIX Adding HTTPS, adding HTTPS redirect"
            a2dissite webtrees
            a2ensite  webtrees-redir
            a2ensite  webtrees-ssl
        fi
    fi
}

auto_wizard
pretty_urls
https

echo "$PREFIX Starting Apache."

exec apache2-foreground
