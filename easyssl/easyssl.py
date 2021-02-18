#!/usr/bin/python3

import os
import sys
from typing import List

from common.utils.platform_utils import execute
from common.easyssl_platform import launch

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CERTS_SCRIPT = f"{CURRENT_DIR}/common/easyssl_chain.sh"
STORE_SCRIPT = f"{CURRENT_DIR}/common/easyssl_store.sh"


def usage():
    print("\nEasySSL helps you to create :\n\n"
          "Platforms: create all the TLS material you need for an entire platform and servers in one "
          "configuration file !\n"
          "Chains: create a complete chain of CAs, private keys and certificates in one short command line !\n"
          "Stores: create a keystores and truststores in one short command line !\n"
          "\n"
          "easyssl platform --help\n"
          "easyssl chain --help\n"
          "easyssl store --help\n"
          "\n"
          "Further usage:\n"
          "easyssl -p #Remove all platforms, chains and stores")


def check_param(argument: str, options: List[str]):
    for option in options:
        if argument == option:
            return True


def purge_all():
    purge = '-p'
    launch([purge])
    execute([STORE_SCRIPT, purge], stream_stdout=True)
    execute([CERTS_SCRIPT, purge], stream_stdout=True)


if __name__ == "__main__":
    # intentionally avoid args parsers
    args: List[str] = sys.argv[1:]

    if check_param(args[0], ["h", "help", "-h", "--help"]):
        usage()
    elif check_param(args[0], ["-p", "--purge"]):
        purge_all()
    elif check_param(args[0], ["chain"]):
        certs_args: List[str] = [CERTS_SCRIPT] + args[1:]
        execute(certs_args, stream_stdout=True)
    elif check_param(args[0], ["store"]):
        store_args: List[str] = [STORE_SCRIPT] + args[1:]
        execute(store_args, stream_stdout=True)
    elif check_param(args[0], ["platform"]):
        platform_args: List[str] = args[1:]
        launch(platform_args)
    else:
        print("! FATAL: Unknown command. Use 'easyssl --help'")
        sys.exit(1)
