#!/usr/bin/env bash

# VARIABLES
ROOT_CA_EXTENSION="ca_root_ext"
size=4096
validity=365
logfile="/tmp/rootca.log"

# FUNCTIONS

# Generate the CA key and certificate
function makeRootCA() {
    # outputs
    private_key="${dir}/private/${name}_root.p8"
    certificate="${dir}/certs/${name}_root.crt"
    ca_file="${dir}/certs/ca.crt"

    # private key
    temp_key="${dir}/private/temp.pem"
    openssl genrsa -out "${temp_key}" "${size}" >> "${logfile}" 2>&1
    openssl pkcs8 -topk8 -in "${temp_key}" -out "${private_key}" -nocrypt
    rm "${temp_key}"

    # certificate
    DC="easyca.com"
    C="FR"
    ST="IdF"
    L="Paris"
    O="KaioKeiCorp"
    OU="EasyCA"
    CN="${name}"
    email="${name}@easyca.com"
    subject="/DC=${DC}/C=${C}/ST=${ST}/L=${L}/O=${O}/OU=${OU}/CN=${CN}/emailAddress=${email}"
    openssl req -config "${config}" -key "${private_key}" -new -x509 -days "${validity}" -sha256 -extensions "${ROOT_CA_EXTENSION}" -out "${certificate}" -subj "${subject}"

    cp "${certificate}" "${ca_file}"
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
    --size)
        size="$2"
        shift 2
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
makeRootCA

exit 0