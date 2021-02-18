import subprocess
from typing import List


CMD_TIMEOUT_SECONDS = 10


def execute(command: List[str], logfile: str = None, user_input: str = None, stream_stdout: bool = False):
    """
    Run a subprocess from the provided command and log into a dedicated logfile
    The subprocess may depends on user input

    :param command: List of params to launch the subprocess (just like a command line)
    :param logfile: Absolute path to a log file to print the command output
    :param user_input: String user input to provide to the launched subprocess
    :param stream_stdout: If true, stream the stdout of the process in console
    :return: A list with process' [return_code, stdout]
    """
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # user input
    if user_input is not None:
        process.communicate(str.encode(user_input), timeout=CMD_TIMEOUT_SECONDS)
    # logfile
    if logfile is not None:
        stdout_file = open(logfile, 'a')
    # process execution
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        elif output:
            output_str = output.decode("utf-8").strip()
            if stream_stdout:
                print(output_str)
            if logfile is not None:
                stdout_file.write(output_str)

    process.terminate()

    if logfile is not None:
        stdout_file.close()

    return int(process.returncode)
