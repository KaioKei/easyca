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
KEYSTORE_P12_NAME="keystore.p12"
KEYSTORE_JKS_NAME="keystore.jks"
TRUSTSTORE_NAME="truststore.jks"

# args
arg_mode="None"
arg_store="None"
arg_cert="None"
arg_key="None"
arg_ca_file="None"
arg_out_dir="/tmp"
arg_alias="None"
arg_pass="None"

# vars
alias_cert="certificate"
alias_ca="ca"
password="None"

# === FUNCTIONS ===
function log_red() {
    printf "${red}%s${end}\n" "$1"
}

function log_green() {
    printf "${grn}%s${end}\n" "$1"
}

function usage(){
  # shellcheck disable=SC2059
  printf "${blu}Overview :${end}

  Create a keystore and a truststore from a provided private key, a certificate and a CA file (Optional)

  ${blu}Usage :${end}
  store.sh [mode] [options]

  ${grn}[ mode ]${end}
  --create\t\tCreate a keystore and a truststore with the provided material
  --import\t\tImport a key, a cert or a CA file inside the provided store

  ${grn}[ options ]${end}
  --key [path]\t\tUser private key.
  --cert [path]\t\tUser certificate.
  --cafile [path]\tUser CA file. Optional. Default is None.
  --store [path]\tKeystore or truststore. Used by '--import' mode only.
  --alias [name]\tName of the cert inside the stores. Optional. Default is 'certificate'.
  --output [path]\tFolder path where the keystore and the truststore are generated. Optional. Default is '/tmp'.

  ${blu}Examples :${end}
  . Create a truststore and a keystore :
  store.sh --create --key server.p8 --cert server.crt --cafile ca.crt --output /tmp/stores

  . Import a certificate inside a truststore :
  store.sh --import --cert server.crt --store truststore.jks

  . Import a CA file inside a keystore :
  store.sh --import -cafile ca.crt --store keystore.jks
  "

}

# Import a CA cert inside a store
# arg1: cert to import
# arg2: output keystore or truststore
# arg3: alias of the cert
# arg4: password of the store
function importCA() {
    yes | keytool -import -trustcacerts -file "$1" -keystore "$2" -storetype jks -storepass "$4" -alias "$3" > /dev/null 2>&1
    printf ". CA file %s imported in %s as %s\n" "$(basename -- "$1")" "$2" "$3"
}

# Import a cert inside a store
# arg1: cert to import
# arg2: output keystore or truststore
# arg3: alias of the cert
# arg4: password of the store
function import() {
    yes | keytool -import -file "$1" -keystore "$2" -storetype jks -storepass "$4" -alias "$3" >/dev/null 2>&1
    printf ". File %s imported in %s as %s\n" "$(basename -- "$1")" "$2" "$3"
}

# if no argument '--alias' was given, set alias according to the cert if provided, or to the ca file if provided
function setAlias(){
    if [ "${arg_alias}" == "None" ]; then
        if [ "${arg_cert}" != "None" ]; then
            cert_filename=$(basename -- "${arg_cert}")
            alias_cert="${cert_filename%.*}"
            alias_ca="ca_${alias_cert}"
        elif [ "${arg_ca_file}" != "None" ]; then
            ca_filename=$(basename -- "${arg_ca_file}")
            alias_ca="${ca_filename%.*}"
        fi
    fi
}

function keystore(){
    echo ". Create keystore"
    # create openssl keystore
    keystore_p12="${arg_out_dir}/${KEYSTORE_P12_NAME}"
    keystore_jks="${arg_out_dir}/${KEYSTORE_JKS_NAME}"
    openssl pkcs12 -export -in "${arg_cert}" -inkey "${arg_key}" -name "${alias_cert}" -passout pass:${password} -out "${keystore_p12}"
    # create java keystore
    keytool -importkeystore -srckeystore "${keystore_p12}" -srcstoretype pkcs12 -srcstorepass "${password}" -destkeystore "${keystore_jks}" -deststoretype jks -deststorepass "${password}" >/dev/null 2>&1
    if [ "${arg_ca_file}" != "None" ]; then
        importCA "${arg_ca_file}" "${keystore_jks}" "${alias_ca}" "${password}"
    fi
}

function truststore(){
    echo ". Create truststore"
    truststore_jks="${arg_out_dir}/${TRUSTSTORE_NAME}"
    if [ "${arg_ca_file}" != "None" ]; then
        importCA "${arg_ca_file}" "${truststore_jks}" "${alias_ca}" "${password}"
    fi
    import "${arg_cert}" "${truststore_jks}" "${alias_cert}" "${password}"
}

# === PARSING ===

POSITIONAL=()
while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
    -h|--help)
      usage
      shift
      exit 0
      ;;
    --create)
      arg_mode="create"
      shift
      ;;
    --import)
      arg_mode="import"
      shift
      ;;
    --store)
      arg_store="$2"
      shift 2
      ;;
    --cert)
      arg_cert="$2"
      shift 2
      ;;
    --key)
      arg_key="$2"
      shift 2
      ;;
    --cafile)
      arg_ca_file="$2"
      shift 2
      ;;
    --alias)
      arg_alias="$2"
      shift 2
      ;;
    --output)
      arg_out_dir="$2"
      shift 2
      ;;
    --pass)
      arg_pass="$2"
      shift 2
      ;;
    *)    # unknown option
      POSITIONAL+=("$1") # save it in an array for later
      shift # past argument
      ;;
  esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# === PROGRAM ===
if [ "${arg_pass}" != "None" ]; then
    password="${arg_pass}"
else
    read -r -s -p "Enter stores password: " password
fi
printf "\n\n"

# define alias
setAlias

# create mode
if [ "${arg_mode}" == "create" ]; then
  log_green "### CREATE STORES ###"
  keystore
  truststore
  log_green ". Done"
  echo ""
  tree "${arg_out_dir}" -L 1
# import mode
elif [ "${arg_mode}" == "import" ]; then
    if [ "${arg_ca_file}" != "None" ]; then
        importCA "${arg_ca_file}" "${arg_store}" "${alias_ca}" "${password}"
    fi
    if [ "${arg_cert}" != "None" ];then
        import "${arg_cert}" "${arg_store}" "${alias_cert}" "${password}"
    fi
    if [ "${arg_key}" != "None" ];then
        import "${arg_key}" "${arg_store}" "${alias_cert}" "${password}"
    fi
fi

echo ""


