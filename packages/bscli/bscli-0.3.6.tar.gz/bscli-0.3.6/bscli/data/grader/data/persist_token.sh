#!/usr/bin/env bash

MYDIR="${0%/*}"
API_NAME=bsapi.json
TOKEN_NAME=token.json
LOCAL_API_CONFIG_PATH=${MYDIR}/${API_NAME}
LOCAL_TOKEN_PATH=${MYDIR}/${TOKEN_NAME}
CONFIG_BASE=~/.config/bscli
API_CONFIG_PATH=${CONFIG_BASE}/${API_NAME}
TOKEN_PATH=${CONFIG_BASE}/${TOKEN_NAME}

if [ ! -f "$LOCAL_API_CONFIG_PATH" ]; then
    echo "ERROR: Could not find local API config file ${LOCAL_API_CONFIG_PATH}"
    exit 1
elif [ ! -f "$LOCAL_TOKEN_PATH" ]; then
    echo "ERROR: Could not find local token file ${LOCAL_TOKEN_PATH}"
    exit 1
fi

echo Persistent API access will be stored in "${CONFIG_BASE}"
mkdir -p "${CONFIG_BASE}"

echo "Installing Brightspace API config (${API_NAME})"
if [ -f "$API_CONFIG_PATH" ]; then
    # Found pre-existing API config, check if it differs
    if diff -q -w "${LOCAL_API_CONFIG_PATH}" "${API_CONFIG_PATH}" > /dev/null; then
        echo "- Skipping (already exists)"
    else
        # Show diff to user and start interactive copy to ask for overwrite confirmation, while making a backup
        echo "- ERROR: ${API_CONFIG_PATH} already exists and differs from ${LOCAL_API_CONFIG_PATH}"
        diff -w -u "${API_CONFIG_PATH}" "${LOCAL_API_CONFIG_PATH}"
        cp -i -b "${LOCAL_API_CONFIG_PATH}" "${API_CONFIG_PATH}" || exit 1
    fi
else
    cp "${LOCAL_API_CONFIG_PATH}" "${API_CONFIG_PATH}"
fi

echo "Installing Brightspace API token (${TOKEN_NAME})"
if [ -f "$TOKEN_PATH" ]; then
    # Found pre-existing API token, check if it differs
    if diff -q -w "${LOCAL_TOKEN_PATH}" "${TOKEN_PATH}" > /dev/null; then
        echo "- Skipping (already exists)"
    else
        # Show diff to user and start interactive copy to ask for overwrite confirmation, while making a backup
        echo "- ERROR: ${TOKEN_PATH} already exists and differs from ${LOCAL_TOKEN_PATH}"
        diff -w -u "${TOKEN_PATH}" "${LOCAL_TOKEN_PATH}"
        cp -i -b "${LOCAL_TOKEN_PATH}" "${TOKEN_PATH}" || exit 1
    fi
else
    cp "${LOCAL_TOKEN_PATH}" "${TOKEN_PATH}"
fi

echo Successfully configured persistent API access