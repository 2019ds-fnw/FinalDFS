#!/bin/bash
set -e
set -u

sudo docker rm -f $(sudo docker container ls -aqf name=dfs)