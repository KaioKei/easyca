#!/usr/bin/env python3
import argparse
import calendar
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Dict

import yaml

from common.impl.material import Material, MaterialFactory
from common.utils.platform_utils import execute

TIMESTAMP = calendar.timegm(time.gmtime())
# program dirs
COMMON_DIR = os.path.dirname(os.path.realpath(__file__))
EASYSSL_DIR = os.path.dirname(COMMON_DIR)
CHAINS_DIR = f"{EASYSSL_DIR}/build/chains"
PLATFORMS_DIR = f"{EASYSSL_DIR}/build/platforms"
PLATFORM_DIR = f"{PLATFORMS_DIR}/platform_{TIMESTAMP}"
# scripts
CERTS_SCRIPT = f"{COMMON_DIR}/easyssl_chain.sh"
STORE_SCRIPT = f"{COMMON_DIR}/easyssl_store.sh"
UTILITY_SCRIPT = f"{COMMON_DIR}/utils/certs_utils.sh"
# resources locations
LOGFILE = f"{EASYSSL_DIR}/logs/platform_{TIMESTAMP}.log"
TRUSTSTORE_LOCATION = f"{PLATFORM_DIR}/truststore.jks"
# names
CA_ALIAS = "ca"
CA_ROOT_DIR_NAME = f"{CA_ALIAS}_root"
CA_INTERMEDIATE_DIR_NAME = f"{CA_ALIAS}_intermediate"
CA_FILE_NAME = "ca_file"
ADMIN_ALIAS = "admin"
CHAINS_SUFFIX_REGEX = "_[0-9]{10}"
EXEC_CHAIN_OUTPUT = "chain_dir: "
# settings
LOCATION_KEY = "location"
CERT_KEY = "cert"
KEY_KEY = "key"
KEYSTORE_KEY = "keystore"
# platform configuration
CONF_ROOT = "platform"
CONF_PASSWORD = "password"
CONF_HOSTS = "hosts"
CONF_HOSTNAME = "hostname"
CONF_IP = "ip"
CONF_USERS = "users"
CONF_CN = "cn"

# inputs
g_conf_hosts: List[Dict[str, str]]
g_platform_servers: List[str]
g_admin_servers: List[str]
g_password: str

# globals
g_ca_root_cert: str
g_ca_intermediate_file: str
g_ca_intermediate_cert: str
g_ca_intermediate_dir: str
# store material informations per entity name. EX:
# {
#   "material_name": {
#     "host_1": {
#       "location": "chain_dir_location"
#       "key": "key_location",
#       "cert": "cert_location"
#     }
#   }
# }
g_material_locations: Dict[str, Dict[str, Dict[str, str]]] = {}


# DEDICATED UTILS #
def print_state(message: str):
    """
    Print a message without a carriage return and is immediately printed, without wainting the code that follows
    """
    print(message, end=' ')
    sys.stdout.flush()


def get_material(root_dir: str, name: str, material: Material):
    return f"{root_dir}/{name}/{material.parent_dir}/{name}.{material.file_type}"


# PLATFORM GENERATION #
def generate_ca_chain():
    ca_cmd: List[str] = [CERTS_SCRIPT, "--intermediate", "--name", CA_ALIAS]
    execute(ca_cmd, LOGFILE)

    # save ca certs
    ca_material = MaterialFactory.get_certificate_material()
    ca_chain_dir = f"{CHAINS_DIR}/{CA_ALIAS}"
    # root
    global g_ca_root_cert
    g_ca_root_cert = \
        f"{ca_chain_dir}/{CA_ROOT_DIR_NAME}/{ca_material.parent_dir}/{CA_ROOT_DIR_NAME}.{ca_material.file_type}"
    # intermediate
    global g_ca_intermediate_dir
    global g_ca_intermediate_file
    global g_ca_intermediate_cert
    g_ca_intermediate_dir = f"{ca_chain_dir}/{CA_INTERMEDIATE_DIR_NAME}"
    g_ca_intermediate_file = f"{g_ca_intermediate_dir}/{ca_material.parent_dir}/{CA_FILE_NAME}.{ca_material.file_type}"
    g_ca_intermediate_cert = \
        f"{g_ca_intermediate_dir}/{ca_material.parent_dir}/{CA_INTERMEDIATE_DIR_NAME}.{ca_material.file_type}"


def generate_truststore():
    import_ca_cmd: List[str] = [STORE_SCRIPT, "--import",
                                "--cafile", g_ca_root_cert,
                                "--store", TRUSTSTORE_LOCATION,
                                "--pass", g_password]
    execute(import_ca_cmd, LOGFILE)
    import_ca_cmd: List[str] = [STORE_SCRIPT, "--import",
                                "--cafile", g_ca_intermediate_cert,
                                "--store", TRUSTSTORE_LOCATION,
                                "--pass", g_password]
    execute(import_ca_cmd, LOGFILE)


def generate_certs_chains():
    for host_conf in g_conf_hosts:
        # if 'users' not configured, only generate a cert named after the hostname
        hostname = host_conf.get(CONF_HOSTNAME)
        users: List[str] = host_conf.get(CONF_USERS) if CONF_USERS in host_conf else [hostname]
        san = f"{hostname},{host_conf.get(CONF_IP)}"
        cn = host_conf.get(CONF_CN)
        # init metadata
        global g_material_locations
        g_material_locations[hostname] = {}
        for user in users:
            create_certs_cmd: List[str] = [CERTS_SCRIPT, "--super",
                                           "--name", user,
                                           "--issuer", g_ca_intermediate_dir,
                                           "--san", san]
            if cn is not None:
                create_certs_cmd = create_certs_cmd + ["--cn", cn]

            execute(create_certs_cmd, LOGFILE)

            # save certs locations in global dictionary for further usage (import in truststore, extraction)
            chain_dir: str = f"{CHAINS_DIR}/{user}"
            cert_location: str = get_material(chain_dir, user, MaterialFactory.get_certificate_material())
            key_location: str = get_material(chain_dir, user, MaterialFactory.get_private_key_material())
            g_material_locations[hostname][user] = {}
            g_material_locations[hostname][user][LOCATION_KEY] = chain_dir
            g_material_locations[hostname][user][KEY_KEY] = key_location
            g_material_locations[hostname][user][CERT_KEY] = cert_location


def generate_keystores():
    keystore_material = MaterialFactory.get_keystore_material()
    for hostname, host_section in g_material_locations.items():
        for username, user_section in host_section.items():
            keystore_parent_dir: str = f"{user_section.get(LOCATION_KEY)}/{username}/{keystore_material.parent_dir}"
            # create keystore
            generate_keystore_cmd: List[str] = [STORE_SCRIPT, "--create",
                                                "--key", user_section.get(KEY_KEY),
                                                "--cert", user_section.get(CERT_KEY),
                                                "--intermediate", g_ca_intermediate_cert,
                                                "--output", keystore_parent_dir,
                                                "--pass", g_password]
            execute(generate_keystore_cmd, LOGFILE)
            # save keystore location
            keystore_location: str = f"{keystore_parent_dir}/{username}-keystore.{keystore_material.file_type}"
            g_material_locations[hostname][username][KEYSTORE_KEY] = keystore_location


def extract():
    print()
    print(g_material_locations)
    # copy ca in platform common dir
    shutil.copy(g_ca_intermediate_file, f"{PLATFORM_DIR}")
    for hostname, host_section in g_material_locations.items():
        # create host folder
        folder_path = Path(f"{PLATFORM_DIR}/{hostname}")
        if not folder_path.exists():
            folder_path.mkdir(parents=True)
        # copy each TLS material inside the dedicated host folder
        for user, user_section in host_section.items():
            shutil.copy(user_section.get(KEYSTORE_KEY), folder_path)
            shutil.copy(user_section.get(CERT_KEY), folder_path)
            shutil.copy(user_section.get(KEY_KEY), folder_path)


# MAIN #
def purge():
    print(". Purge platforms :")
    for root, dirs, files in os.walk(PLATFORMS_DIR):
        for platform in dirs:
            print(f".    {platform}")
            shutil.rmtree(f"{root}/{platform}")
    print(". Done")


def init():
    Path(LOGFILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOGFILE, 'w') as logfile:
        logfile.write("")
    print(". Initialize platform dir ..", end=' ')
    Path(PLATFORM_DIR).mkdir(parents=True)
    print("OK")
    # this file will contain the chain names concerned by this platform
    with open(LOGFILE, 'w') as logfile:
        logfile.write("")


def load_configuration(configuration_file: str):
    global g_conf_hosts
    global g_password
    with open(configuration_file, 'r') as stream:
        try:
            conf = yaml.safe_load(stream).get(CONF_ROOT)
            g_password = conf.get(CONF_PASSWORD)
            g_conf_hosts = conf.get(CONF_HOSTS)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)


def launch(arguments: List[str]):
    # parsing
    parser = argparse.ArgumentParser(description='Generate TLS materials for a list of hosts. TLS material = private '
                                                 'key, public key, CA file, keystore and truststore. The truststore and'
                                                 ' the CA file are common to the entire platform while each private key'
                                                 ', certificate and keystore are dedicated to one single server.')
    parser.add_argument('--conf', dest='configuration', action='store',
                        help='Platform configuration file. Check "conf/platform_conf_example.yml"')
    parser.add_argument('--purge', dest='purge_platforms', action='store_true',
                        help=f"Remove all platforms dir in {PLATFORMS_DIR}")
    args = parser.parse_args(arguments)

    if args.purge_platforms:
        purge()
    else:
        load_configuration(args.configuration)
        init()

        print_state(". Initialize CA ..")
        generate_ca_chain()
        print("OK")
        print_state(". Generate platform truststore ..")
        generate_truststore()
        print("OK")
        print_state(". Generate platform certificates  ..")
        generate_certs_chains()
        print("OK")
        print_state(". Generate keystores ..")
        generate_keystores()
        print("OK")
        print_state(". Extract result ..")
        extract()
        print("OK")

        print(f". Done : {PLATFORM_DIR}")
