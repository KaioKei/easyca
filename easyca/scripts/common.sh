#!/usr/bin/env bash


# create the directories where all the files will be generated
# arg1 : path of the entity directory (root, intermediate, ...)
# arg2 : source path of the openssl configuration for the current entity
function init(){
    cd "$1" || exit
    mkdir certs private csr
    chmod 700 private
    touch index.txt index.txt.attr
    echo 1000 > serial
    cd "${COMMON_DIR}" || exit

    cp "$2" "$1/openssl.cnf"
}

# Configure the CA
# arg1 : name of the entity (root, intermediate, ...)
# arg2 : path of the openssl configuration for the current entity (not the source)
function configure() {
    # openssl conf
    sed -i -e "s+{{ca_name}}+$1+g" "$2/openssl.cnf"
    sed -i -e "s+{{dir}}+$2+g" "$2/openssl.cnf"
}

# params
# arg1: openssl config file path
# arg2: SAN string in format 'ip1,ip2,dns1'
function configureSAN() {
    # uncomment subjectAltName settings in issuer config file
    sed -i -e "s+#subjectAltName = @alt_names+subjectAltName = @alt_names+g" "$1"
    IFS=',' read -ra ADDR <<<"$2"
    before_san_placeholder="#{{before_san}}"
    count_san_ip=1
    count_san_host=1
    for i in "${ADDR[@]}"; do
        if [[ $i =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            # for ip address
            sed -i "s+${before_san_placeholder}+IP\.${count_san_ip} = ${i}\n${before_san_placeholder}+g" "$1"
            count_san_ip=$((count_san_ip + 1))
        else
            # for hostname
            sed -i "s+${before_san_placeholder}+DNS\.${count_san_host} = ${i}\n${before_san_placeholder}+g" "$1"
            count_san_host=$((count_san_host + 1))
        fi
    done
}