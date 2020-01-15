#!/bin/bash

sudo docker container rm -f $(sudo docker container ls -aqf name=minion)
sudo docker container rm -f $(sudo docker container ls -aqf name=master)
sudo docker network rm dfs-network