#!/bin/sh

cd ..
if [ ! -f "Dockerfile" ]; then
  echo you need to execute the script from directory "scripts"
  exit
fi

echo Building docker image ...
sudo docker build -t sysu2019dsfnw/server .

echo Creating docker network ...
sudo docker network create --driver=bridge --subnet=192.168.0.0/16 dfs-network

echo Cleaning previous docker containers ...
sudo docker container rm -f $(sudo docker container ls -aqf name=minion)
sudo docker container rm -f $(sudo docker container ls -aqf name=master)

echo Starting minion-1 ...
sudo docker run -d --rm --network=dfs-network \
       --ip=192.168.1.2 \
       --name=minion-1 \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python minion.py

echo Starting minion-2 ...
sudo docker run -d --rm --network=dfs-network \
       --ip=192.168.1.3 \
       --name=minion-2 \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python minion.py

echo Starting minion-3 ...
sudo docker run -d --rm --network=dfs-network \
       --ip=192.168.1.4 \
       --name=minion-3 \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python minion.py

echo Starting minion-4 ...
sudo docker run -d --rm --network=dfs-network \
       --ip=192.168.1.5 \
       --name=minion-4 \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python minion.py

echo Starting master ...
sudo docker run -it --rm --network=dfs-network \
       -p 2131:2131 \
       --ip=192.168.1.100 \
       --name=master \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python master.py