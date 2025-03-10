#!/bin/bash

if ls /etc/apache2/sites-enabled | grep -q 'ssl';
then
    curl -vs -k --fail https://127.0.0.1:443/ || exit 1
else
    curl -vs --fail http://127.0.0.1:80/ || exit 1
fi
