#!/bin/bash

# https://github.com/fisharebest/webtrees/blob/7f1eef18821463166c14403c3d0e0aa3ba7a4204/app/Http/Middleware/BadBotBlocker.php#L335
# https://github.com/fisharebest/webtrees/blob/7f1eef18821463166c14403c3d0e0aa3ba7a4204/app/Http/Middleware/BadBotBlocker.php#L313-L318
# https://github.com/NathanVaughn/webtrees-docker/issues/164

if ls /etc/apache2/sites-enabled | grep -q 'ssl';
then
    curl --verbose --silent --insecure --fail --cookie-jar /tmp/cookie.txt --cookie "x=y" --cookie /tmp/cookie.txt --user-agent "Chrome/" https://127.0.0.1:443/ || exit 1
else
    curl --verbose --silent --fail --cookie-jar /tmp/cookie.txt --cookie "x=y" --cookie /tmp/cookie.txt --user-agent "Chrome/" http://127.0.0.1:80/ || exit 1
fi
