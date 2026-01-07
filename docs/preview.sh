#!/bin/bash

make html

python3 -m http.server --directory _build/html 8000
