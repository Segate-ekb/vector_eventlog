#!/bin/bash
set -e

docker login -u $DOCKER_LOGIN -p $DOCKER_PASSWORD

if [ "$DOCKER_SYSTEM_PRUNE" = 'true' ] ; then
    docker system prune -af
fi

last_arg='.'
if [ "$NO_CACHE" = 'true' ] ; then
    last_arg='--no-cache .'
fi

echo "Building and pushing for version: $version"
docker build \
    --pull \
    --build-arg VERSION=$version \
    -t segateekb/vector_eventlog:$version \
    -t segateekb/vector_eventlog:latest \
    -f ./Dockerfile \
    $last_arg

docker push segateekb/vector_eventlog:$version    
docker push segateekb/vector_eventlog:latest
