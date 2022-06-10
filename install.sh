#!/bin/bash

APPLICATION="easyca"
CURRENT_PATH="$(realpath "$0")"
CURRENT_DIR="$(dirname "${CURRENT_PATH}")"
grn=$'\e[0;92m'
red=$'\e[0;91m'
end=$'\e[0m'

# FUNCTIONS
function loginfo(){
    printf "${grn}[INFO]${end} %s\n" "$1"
}

function logerror(){
    printf "${red}[ERROR]${end} %s - (%s)\n" "$1" "$0"
}

function check_requirement(){
    if ! eval "$@" >> /dev/null 2>&1 ; then
        echo "! Fatal : missing requirement"
        if [ -n "${*: -1}" ]; then echo "${@: -1}"; fi
        exit 1
    fi
}

function check_requirements(){
    loginfo "Check requirements"
    check_requirement python3.10 --version "Install python3.10 first."
    check_requirement python3.10 -m poetry --version "Install poetry with pyton3.10 first."
}

function install_dependencies(){
    loginfo "Install dependencies"
    python3.10 -m poetry check 1> /dev/null
    python3.10 -m poetry env use "$(which python3.10)" 1> /dev/null
    python3.10 -m poetry install 1> /dev/null
}

function install_environment(){
    loginfo "Install environment"
    env_file="${CURRENT_DIR}/.env"
    cp "${env_file}.origin" "${env_file}"
    sed -i -e "s+{{WORKSPACE}}+${HOME}/.${APPLICATION}+g" "${env_file}"
}


function install_bin() {
    loginfo "Install launcher ./${APPLICATION}"
    bin_dir="${CURRENT_DIR}/bin"
    poetry_env=$(python3.10 -m poetry env info -p)

    mkdir -p "${bin_dir}"
    bin_file="${bin_dir}/${APPLICATION}"
    cat <<EOF > "${bin_file}"
#!/usr/bin/env bash

source "${poetry_env}/bin/activate"
easyca "\$@"
EOF
    chmod +x "${bin_file}"
}

# MAIN
cd "${CURRENT_DIR}" || exit

check_requirements
install_dependencies
install_environment
install_bin

loginfo "OK"
exit 0