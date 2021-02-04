#!/usr/bin/env python3
import argparse
import calendar
import os
import re
import shutil
import subprocess
import sys
import time
from enum import Enum
from getpass import getpass
from pathlib import Path
from typing import List, Dict, Pattern
import yaml

TIMESTAMP = calendar.timegm(time.gmtime())
# program dirs
EASYSSL_DIR = "/home/lca/Projects/personnal/easyssl"
CHAINS_DIR = f"{EASYSSL_DIR}/chains"
PLATFORM_DIR = f"{EASYSSL_DIR}/platforms/platform_{TIMESTAMP}"
# scripts
EASYSSL_SCRIPT = f"{EASYSSL_DIR}/easyssl.sh"
STORE_SCRIPT = f"{EASYSSL_DIR}/bin/store.sh"
UTILITY_SCRIPT = f"{EASYSSL_DIR}/bin/utility.sh"
# resources locations
LOGFILE = f"{EASYSSL_DIR}/log/platform.log"
TRUSTSTORE_LOCATION = f"{PLATFORM_DIR}/truststore.jks"
# names
CA_ALIAS = "ca"
CA_ROOT_DIR_NAME = f"{CA_ALIAS}_root"
CA_INTERMEDIATE_DIR_NAME = f"{CA_ALIAS}_intermediate"
CA_FILE_NAME = "ca_file"
ADMIN_ALIAS = "admin"
CHAINS_SUFFIX_REGEX = "_[0-9]{10}"
# settings
LOCATION_KEY = "location"
CERT_KEY = "cert"
KEY_KEY = "key"
KEYSTORE_KEY = "keystore"
# platform configuration
CONF_ROOT = "platform"
CONF_PASSWORD = "password"
CONF_MATERIAL = "material"
CONF_HOST = "host"
CONF_IP = "ip"
CONF_ADMIN = "admin"

# inputs
g_conf_material: List[Dict[str, str]]
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
#   "server2": {
#     "location": "chain_dir_location"
#     "key": "key_location",
#     "cert": "cert_location"
#   }
# }
g_material_locations: Dict[str, Dict[str, str]] = {}


# CLASS UTILS
class Filetype(Enum):
    DIR = "dir"
    FILE = "file"
    P8 = "p8"
    CRT = "crt"
    JKS = "jks"

    def __str__(self):
        return self.value


class Material:
    file_type: Filetype
    parent_dir: str

    def __init__(self, file_type: Filetype, parent_dir: str):
        self.file_type = file_type
        self.parent_dir = parent_dir


class MaterialFactory(Material):

    @staticmethod
    def get_private_key_material():
        return Material(Filetype.P8, "private")

    @staticmethod
    def get_keystore_material():
        return Material(Filetype.JKS, "private")

    @staticmethod
    def get_certificate_material():
        return Material(Filetype.CRT, "certs")


# UTILITIES #
def execute(command: List[str], user_input: str = None):
    """
    Run a subprocess from the provided command and log into a dedicated logfile
    The subprocess may depends on user input
    :param command: List of params to launch the subprocess (just like a command line)
    :param user_input: String user input to provide to the launched subprocess
    :return: None
    """
    if user_input is not None:
        input_bytes = str.encode(user_input)
        p = subprocess.run(command, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    else:
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

    with open(LOGFILE, 'a') as logfile:
        logfile.write(p.stdout.decode("utf-8"))


def find(root_dir: str, regex: str, filetype: Filetype, exact_match=False):
    """
    Search for a directory inside a root dir, according to a matching regex.
    Raise an error if several directories match the regex
    :param root_dir: where to search the directory
    :param regex: the regex matching the directory to find
    :param filetype: FILETYPE to search, either FILETYPE.FILE or FILETYPE.DIR
    :param exact_match: Default false. If true, the function MUST return one result, or an exception if more than one
                        result is found. If false, returns as much results as found in root dir and sub dirs
    :return: the found directory
    """
    rx = re.compile(regex)

    # get candidates dirs or files according to the provided filetype
    candidates: List[str] = []
    for root, dirs, files in os.walk(root_dir):
        if filetype is Filetype.DIR:
            candidates = candidates + filter_list(dirs, rx)
        elif filetype is Filetype.FILE:
            candidates = candidates + filter_list(files, rx)

    # get matching files or dirs according to the provided regex
    results: List[str] = [f"{root_dir}/{x_dir}" for x_dir in candidates]

    if exact_match and len(results) > 1:
        sys.exit(f"! ERROR: ambigous regex {regex} : multiple results {results} inside {root_dir}")
    elif exact_match:
        return results[0]
    else:
        return results


def filter_list(my_list: List[str], regex: Pattern[str]):
    """
    filter list members by regex
    """
    return list(filter(lambda x: regex.match(x), my_list))


def print_state(message: str):
    """
    Print a message without a carriage return and is immediately printed, without wainting the code that follows
    """
    print(message, end=' ')
    sys.stdout.flush()


# PLATFORM UTILS #
def get_material(root_dir: str, name: str, material: Material):
    return f"{root_dir}/{name}/{material.parent_dir}/{name}.{material.file_type}"


def get_admin_name(basename: str):
    return f"{ADMIN_ALIAS}-{basename}"


# PLATFORM GENERATION #
def generate_ca():
    ca_cmd: List[str] = [EASYSSL_SCRIPT, "--intermediate", "--name", CA_ALIAS]
    execute(ca_cmd)
    save_ca(CA_ALIAS)


def save_ca(alias: str):
    """
    Keep ca root and intermediate locations in global vars
    """
    ca_material = MaterialFactory.get_certificate_material()
    ca_chain_dir = find(CHAINS_DIR, alias + CHAINS_SUFFIX_REGEX, Filetype.DIR, exact_match=True)
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
    execute(import_ca_cmd)
    import_ca_cmd: List[str] = [STORE_SCRIPT, "--import",
                                "--cafile", g_ca_intermediate_cert,
                                "--store", TRUSTSTORE_LOCATION,
                                "--pass", g_password]
    execute(import_ca_cmd)


def generate_certs(name: str, san: str):
    create_certs_cmd: List[str] = [EASYSSL_SCRIPT, "--super",
                                   "--name", name,
                                   "--issuer", g_ca_intermediate_dir,
                                   "--san", san]
    execute(create_certs_cmd)
    # store in global dictionary for further usage (import in truststore, extraction)
    save_certs(name)


def save_certs(name: str):
    chain_dir: str = find(CHAINS_DIR, name + CHAINS_SUFFIX_REGEX, Filetype.DIR, exact_match=True)
    cert_location: str = get_material(chain_dir, name, MaterialFactory.get_certificate_material())
    key_location: str = get_material(chain_dir, name, MaterialFactory.get_private_key_material())
    global g_material_locations
    g_material_locations[name] = {}
    g_material_locations[name][LOCATION_KEY] = chain_dir
    g_material_locations[name][KEY_KEY] = key_location
    g_material_locations[name][CERT_KEY] = cert_location


def generate_certs_wrapper():
    for host_conf in g_conf_material:
        name = host_conf.get(CONF_HOST)
        san = f"{host_conf.get(CONF_HOST)},{host_conf.get(CONF_IP)}"
        generate_certs(name, san)
        # also generate admin if conf triggers it
        if host_conf.get(CONF_ADMIN):
            generate_certs(get_admin_name(host_conf.get(CONF_HOST)), san)


def generate_keystores():
    keystore_material = MaterialFactory.get_keystore_material()
    for material_name, material_section in g_material_locations.items():
        keystore_parent_dir = g_material_locations[material_name][LOCATION_KEY]
        keystore_location: str = f"{keystore_parent_dir}/{material_name}-keystore.{keystore_material.file_type}"
        # create keystore
        generate_keystore_cmd: List[str] = [STORE_SCRIPT, "--create",
                                            "--key", material_section.get(KEY_KEY),
                                            "--cert", material_section.get(CERT_KEY),
                                            "--intermediate", g_ca_intermediate_cert,
                                            "--output", material_section.get(LOCATION_KEY),
                                            "--pass", g_password]
        execute(generate_keystore_cmd)
        # save keystore location
        g_material_locations[material_name][KEYSTORE_KEY] = keystore_location


def trust_certs_ca():
    certs_arg: str = ""
    for dict_section in g_material_locations.values():
        # do not remove the escape char at the end of this string
        certs_arg += f"{dict_section.get(CERT_KEY)} "
    trust_ca_cmd: List[str] = [EASYSSL_SCRIPT, "--trust", g_ca_intermediate_file, certs_arg]
    execute(trust_ca_cmd)


def extract():
    # ca in common dir
    shutil.copy(g_ca_intermediate_file, f"{PLATFORM_DIR}")
    material_hosts = [material.get(CONF_HOST) for material in g_conf_material]
    # materials
    for dir_name in material_hosts:
        # create dirs
        dir_location: str = f"{PLATFORM_DIR}/{dir_name}"
        if not Path(dir_location).exists():
            Path(dir_location).mkdir(parents=True)
        for material_name, material_section in g_material_locations.items():
            if dir_name in material_name:
                shutil.copy(material_section.get(KEYSTORE_KEY), dir_location)
                shutil.copy(material_section.get(CERT_KEY), dir_location)
                shutil.copy(material_section.get(KEY_KEY), dir_location)


# MAIN #
def init():
    # remove the previous logfile
    with open(LOGFILE, 'w') as logfile:
        logfile.write("")
    print(". Purge platforms ..", end=' ')
    for my_dir in os.listdir(f"{EASYSSL_DIR}/platforms/"):
        shutil.rmtree(f"{EASYSSL_DIR}/platforms/{my_dir}")
    print("OK")
    print(". Purge chains ..", end=' ')
    execute([EASYSSL_SCRIPT, "-p"])
    print("OK")
    print(". Initialize platform dir ..", end=' ')
    Path(PLATFORM_DIR).mkdir(parents=True)
    print("OK")


def load_configuration(configuration_file: str):
    global g_conf_material
    global g_password
    with open(configuration_file, 'r') as stream:
        try:
            conf = yaml.safe_load(stream).get(CONF_ROOT)
            g_password = conf.get(CONF_PASSWORD)
            g_conf_material = conf.get(CONF_MATERIAL)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)


def launch():
    print_state(". Initialize CA ..")
    generate_ca()
    print("OK")
    print_state(". Generate platform truststore ..")
    generate_truststore()
    print("OK")
    print_state(". Generate platform certificates  ..")
    generate_certs_wrapper()
    print("OK")
    print_state(". Generate keystores ..")
    generate_keystores()
    print("OK")
    print_state(". Generate platform CA certificate ..")
    trust_certs_ca()
    print("OK")
    print_state(". Extract result ..")
    extract()
    print("OK")

    print(f". Done : {PLATFORM_DIR}")


if __name__ == "__main__":
    # parsing
    parser = argparse.ArgumentParser(description='Generate TLS materials for a list of hosts. TLS material = private '
                                                 'key, public key, CA file, keystore and truststore. The truststore and'
                                                 ' the CA file are common to the entire platform while each private key'
                                                 ', certificate and keystore are dedicated to one single server.')
    parser.add_argument('--conf', dest='configuration', action='store', required=True,
                        help='Platform configuration file. Check "conf/platform_conf_example.yml"')
    args = parser.parse_args()

    load_configuration(args.configuration)
    # sys.exit(0)
    init()
    launch()
