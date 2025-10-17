import sys
import os
import shlex
import subprocess

__all__ = [
    "env_proc_call",
    "env_pip"
]

def env_proc_call(*args,
                  executable=None,
                  text=True,
                  env=None,
                  shell=False,
                  **subprocess_run_kwargs):
    if env is None:
        env = {}
    if executable is None:
        executable = sys.executable

    env['PATH'] = (
                          env.get("PATH", "")
                          + ":" + os.path.dirname(executable)
                          + ":" + os.environ.get("PATH", "")
    ).strip(":")

    if len(args) == 1 and isinstance(args[0], str):
        args = shlex.split(args[0])

    if shell is False:
        prefix = ["{var}='{val}'" for var,val in env.items() if var != "PATH"]
    else:
        prefix = []

    return subprocess.run(
        [*prefix, *args],
        text=text,
        env=env,
        shell=shell,
        **subprocess_run_kwargs
    )

def env_pip(*args):
    return env_proc_call('pip', *args)