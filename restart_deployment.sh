#!/bin/bash

git add .
git commit -m "Improve SPARQL endpoint"
git push

ssh ids2 'cd /data/deploy-ids-tests/rdflib-endpoint ; git pull ; docker-compose down ; docker-compose up -d --build'
