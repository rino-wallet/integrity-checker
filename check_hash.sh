#!/bin/bash
# Get the latest RINO release from GitHub and build it locally.

echo "Starting Integrity Check process..."
cd /frontend
rm -rf build
git fetch --tags
git checkout $(git describe --tags `git rev-list --tags --max-count=1`)
/usr/local/bin/yarn install &&  /usr/local/bin/yarn build:$RINO_ENVIRON
cd /
./check_hash.py