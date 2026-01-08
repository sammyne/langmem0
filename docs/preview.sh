#!/bin/bash

cd `dirname ${BASH_SOURCE[0]}`

set -e

make html

python3 -m http.server --directory _build/html 8000
