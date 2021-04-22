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
STORES_DIR = f"{EASYSSL_DIR}/build/stores"
PLATFORMS_DIR = f"{EASYSSL_DIR}/build/platforms"

# scripts
CERTS_SCRIPT = f"{COMMON_DIR}/easyssl_chain.sh"
STORE_SCRIPT = f"{COMMON_DIR}/easyssl_store.sh"
UTILITY_SCRIPT = f"{COMMON_DIR}/utils/certs_utils.sh"
# resources locations

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
g_platform_dir: str
g_logfile: str
g_truststore_location: str

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
    execute(ca_cmd, g_logfile)

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
    import_ca_cmd: List[str] = [STORE_SCRIPT, "--import-ca", g_ca_root_cert,
                                "--store", g_truststore_location,
                                "--pass", g_password]
    execute(import_ca_cmd, g_logfile)
    import_ca_cmd: List[str] = [STORE_SCRIPT, "--import-ca", g_ca_intermediate_cert,
                                "--store", g_truststore_location,
                                "--pass", g_password]
    execute(import_ca_cmd, g_logfile)


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

            execute(create_certs_cmd, g_logfile)

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
            # create keystore
            generate_keystore_cmd: List[str] = [STORE_SCRIPT, "--create",
                                                "--key", user_section.get(KEY_KEY),
                                                "--cert", user_section.get(CERT_KEY),
                                                "--pass", g_password]
            execute(generate_keystore_cmd, g_logfile)
            # save keystore location
            keystore_location: str = f"{STORES_DIR}/{username}/{username}-keystore.{keystore_material.file_type}"
            g_material_locations[hostname][username][KEYSTORE_KEY] = keystore_location


def extract():
    # copy ca in platform common dir
    # truststore is already present !
    shutil.copy(g_ca_intermediate_file, f"{g_platform_dir}")
    for hostname, host_section in g_material_locations.items():
        # create host folder
        folder_path = Path(f"{g_platform_dir}/{hostname}")
        if not folder_path.exists():
            folder_path.mkdir(parents=True)
        # copy each TLS material inside the dedicated host folder
        for user, user_section in host_section.items():
            shutil.copy(user_section.get(KEYSTORE_KEY), folder_path)
            shutil.copy(user_section.get(CERT_KEY), folder_path)
            shutil.copy(user_section.get(KEY_KEY), folder_path)


# MAIN #
def purge_platforms():
    # remove platform dirs
    for platform in list_platforms():
        print(f". Removed {PLATFORMS_DIR}/{platform}")
        shutil.rmtree(f"{PLATFORMS_DIR}/{platform}")
            

def list_platforms():
    return os.listdir(PLATFORMS_DIR) if Path(PLATFORMS_DIR).exists() else []


def init(platform_name: str):
    # build platform name
    global g_platform_dir
    g_platform_dir = f"{PLATFORMS_DIR}/{platform_name}" if platform_name is not None \
        else f"{PLATFORMS_DIR}/platform_{TIMESTAMP}"

    # check if platform already exists
    if platform_name in list_platforms():
        print(f"! FATAL: platform '{platform_name}' already exists")
        sys.exit(1)

    # create platform dir
    print(". Initialize platform ..", end=' ')
    Path(g_platform_dir).mkdir(parents=True)
    print("OK")

    # create logfile
    global g_logfile
    g_logfile = f"{g_platform_dir}/{platform_name}.log"
    with open(g_logfile, 'w') as logfile:
        logfile.write("")

    # build truststore path
    global g_truststore_location
    g_truststore_location = f"{g_platform_dir}/truststore.jks"


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
    description: str = "Create any TLS material your need for your platform servers.\n" \
                       "Configure hosts, IPs and user names in one YAML configuration file\n" \
                       "The TLS material (CAs, private keys, certificates, keystores and truststores) will be created" \
                       " inside one dedicated directory as output.\n" \
                       "Check a configuration example in easyssl/resources/conf/platform_conf_example.yml\n" \
                       "List platforms with '--list'"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--conf', dest='configuration', action='store',
                        help='Platform configuration file. Check "conf/platform_conf_example.yml"')
    parser.add_argument('-n', '--name', dest='platform_name', action='store',
                        help=f"Platform output name")
    parser.add_argument('-p', '--purge', dest='purge_platforms', action='store_true',
                        help=f"Remove all platforms dir in {PLATFORMS_DIR}")
    parser.add_argument('-l', '--list', dest='list_platforms', action='store_true',
                        help=f"List all platforms in {PLATFORMS_DIR}")
    args = parser.parse_args(arguments)

    if args.purge_platforms:
        purge_platforms()
    elif args.list_platforms:
        for p in list_platforms():
            print(f"{p}")
    else:
        load_configuration(args.configuration)
        init(args.platform_name)

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

        print(f". Done.")
        print(f"\noutput: {g_platform_dir}")
