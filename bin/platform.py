#!/usr/bin/env python3

from typing import List
import subprocess
import os
import re
import sys

EASYSSL_DIR = "/home/lca/Projects/personnal/easyssl"
CHAINS_DIR = f"{EASYSSL_DIR}/chains"
EASYSSL_SCRIPT = f"{EASYSSL_DIR}/easyssl.sh"
STORE_SCRIPT = f"{EASYSSL_DIR}/bin/store.sh"

servers: List[str] = ["server1", "server2", "server3"]
admin_servers: List[str] = ["server2"]

ca_int_file: str = ""


def execute(command: List[str], user_input: str = None):
    if user_input is not None:
        input_bytes = str.encode(user_input)
        p = subprocess.run(command, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    else:
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

    print(f"stdout: {p.stdout}")


def find_dir(root_dir: str, regex: str):
    """
    Search for a directory inside a root dir, according to a matching regex.
    Raise an error if several directories match the regex
    :param root_dir: where to find the directory
    :param regex: the regex matching the directory to find
    :return: the found directory
    """
    rx = re.compile(regex)
    res: List[str] = []
    for root, dirs, files in os.walk(root_dir):
        for found_dir in dirs:
            if rx.match(found_dir):
                res.append(found_dir)

    if len(res) > 1:
        sys.exit(f"! ERROR: ambigous regex {regex} : multiple results {res} inside {root_dir}")
    else:
        return res[0]


def init_ca():
    ca_cmd: List[str] = [EASYSSL_SCRIPT, "--intermediate", "--name", "ca"]
    execute(ca_cmd)


def init_truststore():
    ca_dir_name = find_dir(CHAINS_DIR, "ca_[0-9]{10}")
    ca_dir = f"{CHAINS_DIR}/{ca_dir_name}"
    ca_int_dir = f"{ca_dir}/ca_intermediate"
    ca_file = f"{ca_int_dir}/certs/ca_file.crt"
    truststore_location = f"{ca_int_dir}/certs/truststore.jks"
    import_ca_cmd: List[str] = [STORE_SCRIPT, "--import", "--cafile", ca_file, "--store", truststore_location, "--pass",
                                "secret123"]
    execute(import_ca_cmd, "secret123")


def main():
    print(". Purge chains")
    execute([EASYSSL_SCRIPT, "-p"])
    print(". Initialize CA")
    init_ca()
    print(". Initialize truststore")
    init_truststore()


if __name__ == "__main__":
    main()
