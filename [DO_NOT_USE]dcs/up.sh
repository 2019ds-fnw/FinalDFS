#!/bin/bash
set -e
set -u

ln -sf "$1" docker-compose.yml \
&& docker-compose up -d \
&& rm -f docker-compose.yml