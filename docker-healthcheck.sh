#!/bin/bash

if [[ -z "${HTTPS}" && -z "${SSL}" ]]
then
    curl -vs --fail http://127.0.0.1:80/ || exit 1
else
    curl -vs -k --fail http://127.0.0.1:443/ || exit 1
fi