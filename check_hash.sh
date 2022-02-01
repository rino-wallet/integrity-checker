#!/bin/sh

cd /frontend
rm -rf build
git fetch --tags
git checkout $(git describe --tags `git rev-list --tags --max-count=1`)
/usr/local/bin/yarn install &&  /usr/local/bin/yarn build:$ENVIRON
cd /
./check_hash.py