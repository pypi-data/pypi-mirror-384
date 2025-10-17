#!/usr/bin/bash

set -xe

docker build -t build_parse_int_wheels -f Dockerfile ..

docker run --rm -it build_parse_int_wheels
