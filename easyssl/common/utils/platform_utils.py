import subprocess
from enum import Enum
from re import Pattern
from typing import List


def execute(command: List[str], logfile: str = None, user_input: str = None):
    """
    Run a subprocess from the provided command and log into a dedicated logfile
    The subprocess may depends on user input

    :param command: List of params to launch the subprocess (just like a command line)
    :param logfile: Absolute path to a log file to print the command output
    :param user_input: String user input to provide to the launched subprocess
    :return: A list with process' [return_code, stdout]
    """
    if user_input is not None:
        input_bytes = str.encode(user_input)
        p = subprocess.run(command, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    else:
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

    output: str = p.stdout.decode("utf-8")

    # log in file
    if logfile is not None:
        with open(logfile, 'a') as logfile:
            logfile.write(output)

    return [int(p.returncode), str(output)]


def filter_list(my_list: List[str], regex: Pattern[str]):
    """
    filter list members by regex
    """
    return list(filter(lambda x: regex.match(x), my_list))


class Filetype(Enum):
    DIR = "dir"
    FILE = "file"
    P8 = "p8"
    CRT = "crt"
    JKS = "jks"

    def __str__(self):
        return self.value
