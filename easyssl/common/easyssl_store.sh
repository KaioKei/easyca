#!/bin/bash

# colors
red=$'\e[1;31m'
grn=$'\e[1;32m'
yel=$'\e[1;33m'
blu=$'\e[1;34m'
mag=$'\e[1;35m'
cyn=$'\e[1;36m'
end=$'\e[0m'

# constants
TIME=$(date +%s)
STORE_SCRIPT_PATH="$(realpath "$0")"
COMMON_DIR="$(dirname "${STORE_SCRIPT_PATH}")"
EASYSSL_DIR="$(dirname "${COMMON_DIR}")"
BUILD_STORES_DIR="${EASYSSL_DIR}/build/stores"
BUILD_STORES_FILE="${BUILD_STORES_DIR}/.stores"
KEYSTORE_P12_NAME="keystore.p12"
KEYSTORE_JKS_NAME="keystore.jks"
TRUSTSTORE_NAME="truststore.jks"

# args
arg_mode="None"
arg_store="None"
arg_cert="None"
arg_key="None"
arg_ca_file="None"
arg_alias="None"
arg_pass="None"
arg_chain_name="None"

# vars
alias_cert="certificate"
alias_ca="ca"
password="None"
output_dir="/tmp"

# shellcheck source=src/util.sh
source "${COMMON_DIR}/utils/store_utils.sh"

# === FUNCTIONS ===
function log_red() {
  printf "${red}%s${end}\n" "$1"
}

function log_green() {
  printf "${grn}%s${end}\n" "$1"
}

function usage() {
  # shellcheck disable=SC2059
  printf "${blu}Overview :${end}

  With this script you may create or manage your keystore.
  Create a keystore and a truststore from:
  \t- provided keys
  \t- created chains (check 'easyssl cert --list')
  Import existing keys into existing stores.
  The created stores are built in a dedicated folder. List them with '--list'.


  ${blu}Requirements:${end}
  - Java >= 8
  - Openssl = 1.1.1

  ${blu}Usage :${end}
  store [mode] [options] | [utils]

  ${grn}[ mode ]${end}
  -C,--create\t\tCreate a keystore. If a CA file is provided, also create a truststore
  -I,--import\t\tImport an existing private key or certificate inside an existing store
  -IC,--import-ca\tImport an existing CA file inside an existing store

  ${grn}[ options ]${end}
  -p,--pass [password]\tMANDATORY password of the keystore or of the truststore
  -k,--key [path]\t\tUser private key.
  -c,--cert [path]\t\tUser certificate.
  -ca,--cacert [path]\t\tUser CA file. Optional. Default is None.
  -s,--store [path]\t\tKeystore or truststore. Used by '--import' mode only.
  -a,--alias [name]\t\tName of the cert inside the stores and the stores name. Optional. Default is 'certificate'.
  
  ${grn}[ utils ]${end}
  -l,--list\t\tList created stores
  -p,--purge\t\tRemove all stores

  ${blu}Examples :${end}
  # Create a truststore and a keystore :
  store --create --key server.p8 --cert server.crt --cafile ca.crt --pass secret

  # Import a certificate inside a keystore :
  store --import server.crt --store keystore.jks --pass secret

  # Import a CA file inside a truststore :
  store --import-ca ca.crt --store truststore.jks --pass secret
  "
}

# if no argument '--alias' was given, set alias according to the cert if provided, or to the ca file if provided
function set_alias() {
  if [ "${arg_alias}" == "None" ]; then
    if [ "${arg_cert}" != "None" ]; then
      cert_filename=$(basename -- "${arg_cert}")
      alias_cert="${cert_filename%.*}"
      alias_ca="ca-${alias_cert}"
    elif [ "${arg_ca_file}" != "None" ]; then
      ca_filename=$(basename -- "${arg_ca_file}")
      alias_ca="${ca_filename%.*}"
    fi
  else
    alias_cert="${arg_alias}"
    alias_ca="ca-${arg_alias}"
  fi
}

function set_password() {
  if [ "${arg_pass}" != "None" ]; then
    password="${arg_pass}"
  else
    log_red "! FATAL: You must provide option '--pass'. Use 'store -h' to check options."
    exit 1
  fi
}

function make_output() {
  output_dir="${BUILD_STORES_DIR}/${alias_cert}"
  if [ -d "${output_dir}" ]; then
    log_red "! FATAL: already created '${alias_cert}' stores. Use '--alias'"
    exit 1
  else
    mkdir -p "${output_dir}"
  fi
}

function load_chain_material() {
  chain_dir="${EASYSSL_DIR}/build/chains/${arg_chain_name}"
  if [ -d "${chain_dir}" ]; then
    # shellcheck source=src/util.sh
    source "${chain_dir}/.material"

  else
    log_red "! FATAL: no chain named ${arg_chain_name}"
    exit 1
  fi
}

# Import a CA cert inside a store
# arg1: cert to import
# arg2: output keystore or truststore
# arg3: alias of the cert
# arg4: password of the store
function import_ca() {
  yes | keytool -import -trustcacerts -file "$1" -keystore "$2" -storetype jks -storepass "$4" -alias "$3" >/dev/null 2>&1
  printf ". CA %s imported in %s as %s\n" "$(basename -- "$1")" "$(basename -- "$2")" "$3"
}

# Import a cert inside a store
# arg1: cert to import
# arg2: output keystore or truststore
# arg3: alias of the cert
# arg4: password of the store
function import_cert() {
  yes | keytool -import -file "$1" -keystore "$2" -storetype jks -storepass "$4" -alias "$3" >/dev/null 2>&1
  printf ". File %s imported in %s as %s\n" "$(basename -- "$1")" "$(basename -- "$2")" "$3"
}

function keystore() {
  echo ". Create keystore"
  keystore_p12="${output_dir}/${alias_cert}-${KEYSTORE_P12_NAME}"
  keystore_jks="${output_dir}/${alias_cert}-${KEYSTORE_JKS_NAME}"
  openssl pkcs12 -export -in "${arg_cert}" -inkey "${arg_key}" -name "${alias_cert}" -passout pass:${password} -out "${keystore_p12}"
  # create java keystore
  keytool -importkeystore -srckeystore "${keystore_p12}" -srcstoretype pkcs12 -srcstorepass "${password}" -destkeystore "${keystore_jks}" -deststoretype jks -deststorepass "${password}" >/dev/null 2>&1
}

function truststore() {
  echo ". Create truststore"
  truststore_jks="${output_dir}/${alias_cert}-${TRUSTSTORE_NAME}"
  if [ "${arg_ca_file}" != "None" ]; then
    import_ca "${arg_ca_file}" "${truststore_jks}" "${alias_ca}" "${password}"
  fi
}

# === PARSING ===

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
  -h | --help)
    usage
    shift
    exit 0
    ;;
  -P | --pass)
    arg_pass="$2"
    shift 2
    ;;
  -C | --create)
    arg_mode="create"
    shift
    ;;
  -I,--import)
    arg_mode="import"
    arg_cert="$2"
    shift 2
    ;;
  -IC,-import-ca)
    arg_mode="import_ca"
    arg_ca_file="$2"
    shift 2
    ;;

  -l | --list)
    list_stores
    exit 0
    ;;
  -p | --purge)
    purge_stores
    exit 0
    ;;

  --chain)
    arg_chain_name="$2"
    shift 2
    ;;
  -s | --store)
    arg_store="$2"
    shift 2
    ;;
  -c | --cert)
    arg_cert="$2"
    shift 2
    ;;
  -k | --key)
    arg_key="$2"
    shift 2
    ;;
  -ca | --cacert)
    arg_ca_file="$2"
    shift 2
    ;;
  -a | --alias)
    arg_alias="$2"
    shift 2
    ;;
    *) # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift              # past argument
    ;;
  esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# === PROGRAM ===
set_password
set_alias

# create mode
if [ "${arg_mode}" == "create" ]; then
  make_output

  log_green "### CREATE STORES ###"
  keystore
  truststore

  echo ""
  echo "output: ${output_dir}"
  echo "${output_dir}" >>"${BUILD_STORES_DIR}/.stores"
  echo "${alias_cert}" >"${output_dir}/.name"
# import mode
elif [ "${arg_mode}" == "import" ]; then
  import_cert "${arg_cert}" "${arg_store}" "${alias_cert}" "${password}"
  echo "output: ${arg_store}"
elif [ "${arg_mode}" == "import_ca" ]; then
  import_ca "${arg_ca_file}" "${arg_store}" "${alias_ca}" "${password}"
  echo "output: ${arg_store}"
fi

echo ""
