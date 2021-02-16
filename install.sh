#!/bin/bash

CURRENT_PATH="$(realpath "$0")"
CURRENT_DIR="$(dirname "${CURRENT_PATH}")"
ln -s "${CURRENT_DIR}/easyssl/easyssl.py" /usr/local/bin/easyssl
