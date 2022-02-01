# RINO Integrity Checker

A tool for verifying RINO wallet frontend build integrity.
It is implemented as a Docker container running cron job that is calculating hashes needed to ensure frontend integrity.

## How to build and run

### Local environment

1. Build docker image: `docker build -t integrity-checker .`
2. Run docker container with a built image: `docker run $(pwd)/output/:/output/ integrity-checker`

Code is assuming there is /output/ directory that resulting index.html file is created at.
Feel free to customise ths tool to your needs

### AWS

(TODO)