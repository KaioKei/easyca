#!/bin/bash

exec 2>&1

#############
# FUNCTIONS #
#############

# check if arg1 (list[string]) contains arg2 (string)
# returns 'yes' or 'no'
function contains() {
    count=0
    all="$*"
    search="${*: -1}"
    res='no'
    for string in $all; do
        if [ "$search" == "$string" ]; then
            count=$((count + 1))
            if [ $count -ge 2 ]; then
                res='yes'
            fi
        fi
    done

    echo "$res"
}

########
# INIT #
########

# get easyssl chain path
chains_dir="/home/lca/Projects/personnal/easyssl/chains"
CERTS=("pem jks p12 pkcs12")
servers=("server1" "server2" "server3" "server4" "server5")
admin_servers=("server2" "server3")
SAN="server1,172.28.128.22,server2,172.28.128.22,server3,172.28.128.23,server4,172.28.128.24,server5,172.28.128.25"
#servers=("localhost")
#admin_servers=("localhost")
#SAN="localhost,127.0.0.1"
password="secret123"

echo ". Purging chains"
easyssl -p >/dev/null 2>&1
extract_path=/tmp/certs
if [ ! -d ${extract_path} ]; then
    mkdir -p ${extract_path}
else
    rm -rf "${extract_path:?}"/*
fi

#########
# CERTS #
#########

# CA
echo ". Initialize platform root CA"
easyssl --intermediate --name ca >/dev/null 2>&1
ca=$(find "$chains_dir" -maxdepth 1 -type d -name "ca_*")
ca_root_cert="${ca}/ca_root/certs/ca_root.crt"
ca_int="${ca}/ca_intermediate"
ca_int_cert="${ca_int}/certs/ca_intermediate.crt"
echo "int cert : $ca_int_cert"
echo "root cert : $ca_int_cert"

exit

# Punch truststore
echo ". Initialize platform truststore"
truststore_jks="${ca}/ca_intermediate/certs/truststore.jks"
yes | keytool -import -v -trustcacerts -file "${ca_root_cert}" -keystore "${truststore_jks}" -storetype jks -storepass "${password}" -alias "ca_root" >/dev/null 2>&1
yes | keytool -import -v -trustcacerts -file "${ca_int_cert}" -keystore "${truststore_jks}" -storetype jks -storepass "${password}" -alias "ca_intermediate" >/dev/null 2>&1

echo ". Generate certs :"
# admin
printf "\t. admin\n"
for server in ${admin_servers[*]}; do
    alias="admin-${server}"
    # admin key certs
    easyssl --super --name "${alias}" --san "${SAN}" --issuer "${ca_int}" > /dev/null 2>&1
    # admin keystores
    admin_chain_dir=$(find "${chains_dir}" -maxdepth 1 -type d -name "${alias}*")
    admin_key="${admin_chain_dir}/${alias}/private/${alias}.p8"
    admin_cert="${admin_chain_dir}/${alias}/certs/${alias}.crt"
    admin_keystore_p12="${admin_chain_dir}/${alias}/certs/${alias}-keystore.p12"
    admin_keystore_jks="${admin_chain_dir}/${alias}/certs/${alias}-keystore.jks"
    # pkcs12
    openssl pkcs12 -export -in "${admin_cert}" -inkey "${admin_key}" -name "${alias}" -passout pass:${password} -out "${admin_keystore_p12}"
    # jks : import pkcs12 keystore as key and cert entries
    keytool -importkeystore -srckeystore "${admin_keystore_p12}" -srcstoretype pkcs12 -srcstorepass "${password}" -destkeystore "${admin_keystore_jks}" -deststoretype jks -deststorepass "${password}" >/dev/null 2>&1
    yes | keytool -import -trustcacerts -file "${ca_root_cert}" -keystore "${admin_keystore_jks}" -storetype jks -storepass "${password}" -alias "ca_root" >/dev/null 2>&1
    yes | keytool -import -trustcacerts -file "${ca_int_cert}" -keystore "${admin_keystore_jks}" -storetype jks -storepass "${password}" -alias "ca_intermediate" >/dev/null 2>&1
    # truststore
    yes | keytool -import -file "${admin_cert}" -keystore "${truststore_jks}" -storetype jks -storepass "${password}" -alias "${alias}" >/dev/null 2>&1
done

#servers
for server in ${servers[*]}; do
    printf "\t. %s\n" "${server}"
    # server key cert
    easyssl --super --name "${server}" --san "${SAN}" --issuer "${ca_int}" >/dev/null 2>&1
    # server keystore
    server_chain_dir=$(find "${chains_dir}" -maxdepth 1 -type d -name "${server}*")
    server_key="${server_chain_dir}/${server}/private/${server}.p8"
    server_cert="${server_chain_dir}/${server}/certs/${server}.crt"
    server_keystore_p12="${server_chain_dir}/${server}/certs/${server}-keystore.p12"
    server_keystore_jks="${server_chain_dir}/${server}/certs/${server}-keystore.jks"
    # pkcs12
    openssl pkcs12 -export -in "${server_cert}" -inkey "${server_key}" -name "${server}" -passout pass:${password} -out "${server_keystore_p12}"
    # jks: import ca root as trusted ca cert, then the private key and the certificate
    keytool -importkeystore -srckeystore "${server_keystore_p12}" -srcstoretype pkcs12 -srcstorepass "${password}" -destkeystore "${server_keystore_jks}" -deststoretype jks -deststorepass "${password}" >/dev/null 2>&1
    yes | keytool -import -trustcacerts -file "${ca_root_cert}" -keystore "${server_keystore_jks}" -storetype jks -storepass "${password}" -alias "ca_root" >/dev/null 2>&1
    yes | keytool -import -trustcacerts -file "${ca_int_cert}" -keystore "${server_keystore_jks}" -storetype jks -storepass "${password}" -alias "ca_intermediate" >/dev/null 2>&1
    # truststore
    yes | keytool -import -file "${server_cert}" -keystore "${truststore_jks}" -storetype jks -storepass "${password}" -alias "${server}" >/dev/null 2>&1
done

exit 0

######
# CA #
######

# extract certs
easyssl --extract ${extract_path} #>/dev/null 2>&1

# platform CA
echo ". Generate platform CA"
ca_file="${extract_path}/ca.pem"
cp "${ca_int}/certs/ca-intermediate-chain.pem" "${ca_file}"
certs=$(find "${extract_path}" -type f -name "*cert.pem")
easyssl --trust "${ca_file}" "${certs}" >/dev/null 2>&1

###############
# DIRECTORIES #
###############

echo ". Extract certificates"
extract_dir=$(find "${extract_path}" -type d -name "extract*")

# extract server certs
for server in ${servers[*]}; do
    # create servers dirs
    server_dir="${extract_path}/${server}"
    mkdir -p "${server_dir}"
    cp "${ca_file}" "${server_dir}"
    cp "${truststore_jks}" "${server_dir}"
    extract_server_dir=$(find "${extract_dir}" -type d -name "${server}*")
    for cert in ${CERTS[*]}; do
        find "${extract_server_dir}" -name \*."${cert}" -exec cp {} "${server_dir}" \; > /dev/null 2>&1
    done
done

for server in ${admin_servers[*]}; do
    server_dir="${extract_path}/${server}"
    extract_admin_server_dir=$(find "${extract_dir}" -type d -name "admin-${server}*")
    for cert in ${CERTS[*]}; do
        res=$(find "${extract_admin_server_dir}" -name \*."${cert}")
        find "${extract_admin_server_dir}" -name \*."${cert}" -exec cp {} "${server_dir}" \; > /dev/null 2>&1
    done
done

#############
# TERMINATE #
#############

# delete extract
rm "${ca_file}"
rm "${truststore_jks}"
to_delete=$(find ${extract_path} -type d -name "extract*")
for dir in $to_delete; do
    rm -rf "$dir"
done

# DONE
echo ". Done :"
echo ""
tree -L 1 ${extract_path}

exit 0
