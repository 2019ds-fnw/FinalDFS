#!/bin/sh

cd ..
if [ ! -f "Dockerfile" ]; then
  echo you need to execute the script from directory "scripts"
  exit
fi

echo Building docker image ...
sudo docker build -t sysu2019dsfnw/server .

echo Creating docker network ...
sudo docker network create --driver=bridge --subnet=192.168.128.0/24 dfs-network

echo Cleaning previous docker containers ...
sudo docker container rm -f $(sudo docker container ls -aqf name=minion)
sudo docker container rm -f $(sudo docker container ls -aqf name=master)


for i in $(seq 1 12)
do
  echo Starting minion-${i}
  sudo docker run -d --network=dfs-network \
       --ip=192.168.128.$(expr $i + 10) \
       --name=minion-${i} \
       --restart=always \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python minion.py
done

echo Starting master ...
sudo docker run -it --network=dfs-network \
       -p 2131:2131 \
       --ip=192.168.128.254 \
       --name=master \
       --restart=always \
       -v /home/libre/PycharmProjects/FinalDFS/src/:/root:ro \
       sysu2019dsfnw/server \
       python master.py