import pathlib
import subprocess
import sys


def main():
    command = pathlib.Path(__file__).parent / "sourcery"
    return subprocess.call([str(command), *sys.argv[1:]], bufsize=0)
