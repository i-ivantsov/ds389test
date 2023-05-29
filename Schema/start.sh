#!/bin/bash

docker container stop c389ds
docker container rm c389ds
docker volume rm 389ds2.4

docker volume create 389ds2.4
chmod +x *.sh
docker build \
    --build-arg HTTPS_PROXY=${HTTPS_PROXY} \
    --build-arg https_proxy=${https_proxy} \
    --build-arg HTTP_PROXY=${HTTP_PROXY} \
    --build-arg http_proxy=${http_proxy} \
    -t custom389ds:2.4 .
docker run -v 389ds2.4:/data -p 3389:3389 -p 3636:3636 -d --restart unless-stopped --name c389ds -e DS_DM_PASSWORD="test" custom389ds:2.4

