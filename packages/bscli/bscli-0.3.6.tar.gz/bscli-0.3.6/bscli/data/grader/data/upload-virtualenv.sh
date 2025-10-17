#!/usr/bin/env bash

MYDIR="${0%/*}"
CONFIG_BASE=~/.config/bscli
API_CONFIG_PATH=${CONFIG_BASE}/bsapi.json
TOKEN_PATH=${CONFIG_BASE}/token.json

pushd ${MYDIR}

echo [+] Creating venv...
virtualenv venv
cd venv
source bin/activate

echo
echo [+] Installing dependencies...
python3 -m pip install brightspace-api
python3 -m pip install bscli

echo
echo [+] Running upload script

if [ -f "${API_CONFIG_PATH}" ] && [ -f "${TOKEN_PATH}" ] && [ "$1" != "--force-local" ]; then
    echo [i] Using persistent API access
    python3 -m bscli.main feedback upload ../..
else
    echo [i] Using local API access
    if [ "$1" != "--force-local" ]; then
        echo [i] Run ./data/persist_token.sh afterwards for persistent API access
    fi
    python3 -m bscli.main --config-dir .. feedback upload ../..
fi

echo
echo [+] Removing venv
deactivate
cd ..
rm -rf venv/

popd
