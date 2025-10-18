import logging
import os
import subprocess

from cli.toolchain import Toolchain


def run_test(toolchain: Toolchain, args):
    if toolchain.pytest_executable is None:
        logging.warning("Pytest executable not found, skipping test.")
        return -1
    cmd = ['pytest'] + args.backend_args
    logging.debug(' '.join(cmd))
    shell_mode = os.name == "nt"
    result = subprocess.run(cmd, shell=shell_mode)
    return result.returncode
