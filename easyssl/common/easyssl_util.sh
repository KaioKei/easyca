#!/usr/bin/env bash


function util_usage(){
  printf "utils:

  Usage:
  [option] [cert]

  [options]
  --subject   Dump the subject name of the cert
  --san       Dump the Subject Alternative Name of the cert
  "
}

function subject(){
  output=$(openssl x509 -subject -nameopt RFC2253 -noout -in "$1")
  # only display what comes after '='
  echo "${output#*=}"
}

function san(){
  output=$(openssl x509 -text -noout -in "$1" | grep "Subject Alternative Name" -A1 )
  echo ${output#*:}
}

# === PARSING ===

UTIL_POSITIONAL=()
while [[ $# -gt 0 ]]; do
    util_key="$1"
    case $util_key in
    --subject)
        subject "$2"
        exit $?
        ;;
    --san)
        san "$2"
        exit $?
        ;;
    *) # unknown option
        UTIL_POSITIONAL+=("$1") # save it in an array for later
        shift              # past argument
        ;;
    esac
done
set -- "${UTIL_POSITIONAL[@]}" # restore positional parameters