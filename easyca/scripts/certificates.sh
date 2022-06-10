#!/usr/bin/env bash

# VARIABLES
INTERMEDIATE_EXTENSION="ca_intermediate_ext"
CERT_EXTENSION="node_cert"
size=4096
validity=365
MD=sha256
logfile="/tmp/rootca.log"
node=false

# FUNCTIONS

# Create all the node or intermediate certificates
function makeNode() {
    if [ "${node}" == true ]; then
        private_key="${dir}/private/${cn}.p8"
        certificate="${dir}/certs/${cn}.crt"
        csr="${dir}/csr/${cn}.csr.pem"
        extension="${CERT_EXTENSION}"
    else
        private_key="${dir}/private/${name}_intermediate.p8"
        certificate="${dir}/certs/${name}_intermediate.crt"
        csr="${dir}/csr/${name}.csr.pem"
        extension="${INTERMEDIATE_EXTENSION}"
    fi
    ca_file="${dir}/certs/ca.crt"

    # private key
    temp_key="${dir}/private/temp.pem"
    openssl genrsa -out "${temp_key}" "${size}" #>> "${logfile}" 2>&1
    openssl pkcs8 -topk8 -in "${temp_key}" -out "${private_key}" -nocrypt
    rm "${temp_key}"

    # signing request
    DC="easyca.com"
    C="FR"
    ST="IdF"
    L="Paris"
    O="KaioKeiCorp"
    OU="EasyCA"
    email="${cn}@easyca.com"
    subject="/DC=${DC}/C=${C}/ST=${ST}/L=${L}/O=${O}/OU=${OU}/CN=${cn}/emailAddress=${email}"
    # openssl req -new -config "${conf}" -sha256 -key "${private_key}" -x509 -days ${VALIDITY} -extensions "${cert_extension}" -out "${csr}" -subj "${subject}"
    openssl req -new -config "${config}" -${MD} -key "${private_key}" -out "${csr}" -subj "${subject}"

    # certificate
    # if the key must be signed by a provided ca with an absolute path as argument
    yes yes | openssl ca -config "${issuer}/openssl.cnf" -extensions "${extension}" -days ${validity} -notext -md "${MD}" -in "${csr}" -out "${certificate}" #>> "${logfile}" 2>&1

    if [ "${node}" != true ]; then
        echo ". Create the CA file"
        cat "${certificate}" "${issuer}/certs/ca.crt" > "${ca_file}"
    fi
}

# PARSING
# ca_dir : the root directory of the CA. It will be created to contain all the keys, certificates, etc ...
# ca_name : the name of the CA
# ca_config : the openssl configuration source of the CA. It will be copied and configured inside the proper dir.
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
    --dir)
        dir="$2"
        shift 2
        ;;
    --name)
        name="$2"
        shift 2
        ;;
    --config)
        config="$2"
        shift 2
        ;;
    --issuer)
        # directory of the issuer
        issuer="$2"
        shift 2
        ;;
    --size)
        size="$2"
        shift 2
        ;;
    --san)
        san="$2"
        shift 2
        ;;
    --cn)
        cn="$2"
        shift 2
        ;;
    --node)
        node=true
        shift
        ;;
    *) # unknown option
        POSITIONAL+=("$1") # save it in an array for later
        shift              # past argument
        ;;
    esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters


# MAIN
current_script="$(realpath "$0")"
current_dir="$(dirname "${current_script}")"
source "${current_dir}/common.sh"

init "${dir}" "${config}"
configure "${name}" "${dir}"
if [ "${node}" == true ]; then
    configureSAN "${issuer}/openssl.cnf" "${san}"
fi
makeNode

exit 0