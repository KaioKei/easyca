#!/bin/bash

# colors
red=$'\e[1;31m'
grn=$'\e[1;32m'
yel=$'\e[1;33m'
blu=$'\e[1;34m'
mag=$'\e[1;35m'
cyn=$'\e[1;36m'
end=$'\e[0m'

TIME=$(date +%s)
# === FUNCTIONS ===

function log_red() {
    printf "${red}%s${end}\n" "$1"
}

function log_green() {
    printf "${grn}%s${end}\n" "$1"
}

# Remove all dirs referenced inside the file .chains
function purgeDirs() {
    # purge chains
    # shellcheck disable=SC2153
    if [ -f "${CHAINS_FILE}" ]; then
        chains=$(cat "${CHAINS_FILE}")
        for chain in $chains; do
            rm -rf "$chain"
            printf ". Removed %s\n" "${chain}"
        done
        rm "${CHAINS_FILE}"
    fi
}

function subject(){
  output=$(openssl x509 -subject -nameopt RFC2253 -noout -in "$1")
  # only display what comes after '='
  echo "${output#*=}"
}

function extract(){
  if [[ $HEADER = '/*'* ]]; then
    log_red "! FATAL: you must provide absolute path. Try '--help'."
    exit 1
  fi

  # for each chain, extract all certs inside a dedicated directory
  chains=$(cat "${CHAINS_DIR}/.chains")
  extract_dir="$1/extract_${TIME}"
  for chain_source_dir in ${chains[*]}
  do
    chain_name=$(cat "${chain_source_dir}/.name")
    chain_extract_dir="${extract_dir}/${chain_name}"
    # create chain dir
    mkdir -p "${chain_extract_dir}"
    cp "${chain_source_dir}/${chain_name}/certs/"*.crt "${chain_extract_dir}" >> /dev/null 2>&1
    cp "${chain_source_dir}/${chain_name}/private/"*.p8 "${chain_extract_dir}" >> /dev/null 2>&1
  done

  echo ""
  echo "output: ${extract_dir}"
}

# add one or multiple certificates to trust inside a ca file
# if the ca file does not exists, it is created with the provided cert
# else the certificates are simply concatenated at the top of the ca file, keeping the order as they are provided
# arg1: absolute path to the ca file
# arg@:2 : certificates to trust
function trust(){
  ca_file="$1"
  if [ ! -f "${ca_file}" ]; then
      touch "${ca_file}"
  fi
  # shellcheck disable=SC2124
  certs=${@:2}
  cp "${ca_file}" "${ca_file}.backup"
  # do not double quote 'certs' to preserve array
  cat ${certs} "${ca_file}.backup" > "${ca_file}"
  printf ". CA file updated in %s\n" "${ca_file}"
}

function list(){
    chains_file="${CHAINS_DIR}/.chains"
    if [ -f "${chains_file}" ];then
        chains=$(cat "${CHAINS_DIR}/.chains")
        for chain_source_dir in ${chains[*]}
        do
            chain_name=$(basename "${chain_source_dir}")
            echo "$chain_name"
        done
    fi
}
