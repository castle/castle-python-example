#!/usr/bin/env bash
# Point the example app at a specific Castle Python SDK source.
#
#   set-sdk-version.sh develop   -> track the SDK's develop branch (pre-release testing)
#   set-sdk-version.sh 7.3.0     -> pin the released >=7.3.0,<8 package from PyPI
#
# Rewrites the castle requirement in requirements.txt.
set -euo pipefail

target="${1:?usage: set-sdk-version.sh <develop|X.Y.Z>}"

python3 - "$target" <<'PY'
import re
import sys

target = sys.argv[1]
path = "requirements.txt"
with open(path) as f:
    content = f.read()

if target == "develop":
    line = "castle @ git+https://github.com/castle/castle-python.git@develop"
else:
    major = int(target.split(".")[0])
    line = f"castle>={target},<{major + 1}"

updated, count = re.subn(r"^castle\b.*$", line, content, flags=re.M)
if count == 0:
    sys.exit("no castle requirement found in requirements.txt")
with open(path, "w") as f:
    f.write(updated)
PY
