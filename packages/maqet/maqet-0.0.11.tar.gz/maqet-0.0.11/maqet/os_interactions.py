import subprocess
import sys
import os
import signal

from benedict import benedict

from maqet.logger import LEVELS, LOG



def shell_command(command: str, verbose: bool = True) -> benedict:
    """
    Run shell command and return dictionary of stdout, stderr, returncode
    Return is benedict object, members can be accessed as fields
    """
    command = " ".join(command.split())

    proc = subprocess.Popen(command, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid)
    try:
        out = proc.communicate()
    except KeyboardInterrupt:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait()
        raise

    output = benedict({
        "stdout": out[0].decode('ascii').strip("\n"),
        "stderr": out[1].decode('ascii').strip("\n"),
        "rc": proc.returncode
    })

    message = f"command `{command}` returned {output}"

    if verbose:
        level = LEVELS['DEBUG']
        if output.stderr != '':
            level = LEVELS['WARNING']
        if output.rc != 0:
            level = LEVELS['ERROR']

        LOG.log(level, message)
    return output
