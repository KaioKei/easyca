#!/bin/bash

EASYSSL_SCRIPT="$(realpath "$0")"
EASYSSL_DIR="$(dirname "${EASYSSL_SCRIPT}")"
CERTS_SCRIPT="${EASYSSL_DIR}/my_common/easyssl_certs.sh"
STORE_SCRIPT="${EASYSSL_DIR}/my_common/easyssl_store.sh"
PLATFORM_SCRIPT="${EASYSSL_DIR}/my_common/easyssl_platform.py"

function usage() {
    printf "Usage :

    easyssl.sh [mode] [options]

    [mode]
    certs\tCreate or manage your TLS certificates and keys, with a CA root and an intermediate CA
    store\tCreate or manage your keystores
    platform\tCreate your TLS certificates, keys and keystores with CAs for an entire platform

    [example]
    easyssl.sh certs -h
    easyssl.sh store -h
    easyssl.sh platform -h"
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    -h | --help)
        usage
        exit 0
        ;;
    certs)
        exec "${CERTS_SCRIPT}" "${@:2}"
        exit 0
        ;;
    store)
        exec "${STORE_SCRIPT}" "${@:2}"
        exit 0
        ;;
    platform)
        exec python3 "${PLATFORM_SCRIPT}" "${@:2}"
        exit 0
        ;;
    *) # unknown option
        usage
        exit 1
        ;;
    esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters