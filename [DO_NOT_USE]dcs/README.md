# Docker Compose Files

This directory contains multiple `docker-compose` file to start the project with docker environment.

## How to run

Execute following commands:

```shell script
# it will create a soft link named docker-compose.yml 
# to the specified file
# and then delete the soft link
./up.sh <one_of_these_compose_file_name>
```

Example:

```shell script
./up.sh v1.yml
```

## How to stop

You can't stop cluster by executing `docker-compose stop` because the `docker-compose.yml` is deleted by `up.sh`.

> Of course, you can stop or remove containers and corresponding images manually.

Instead, you could clean containers which is started by `up.sh` by executing:

```shell script
./clean.sh
```

Warning: It will remove the related containers irreversibly! (More precisely, any containers whose name starts with "dfs").

