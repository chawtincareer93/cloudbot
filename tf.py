"""Thin wrapper around the terraform CLI."""
import subprocess
from pathlib import Path


def run(args: list[str], cwd: Path, stream: bool = False) -> tuple[int, str]:
    cmd = ["terraform", *args, "-no-color"] if args[0] != "init" else ["terraform", *args, "-no-color"]
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = []
    for line in p.stdout:
        out.append(line)
        if stream:
            print(line, end="")
    p.wait()
    return p.returncode, "".join(out)


def init(cwd):      return run(["init", "-input=false"], cwd)
def validate(cwd):  return run(["validate"], cwd)
def plan(cwd):      return run(["plan", "-input=false", "-out=tfplan"], cwd)
def apply(cwd):     return run(["apply", "-input=false", "tfplan"], cwd, stream=True)
def destroy(cwd):   return run(["destroy", "-input=false", "-auto-approve"], cwd, stream=True)
