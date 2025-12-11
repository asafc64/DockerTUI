#!/bin/bash
docker rm -f demo_nginx demo_redis demo_postgres demo_busybox demo_alpine
docker rm -f compose_web compose_db compose_cache compose_worker