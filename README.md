# RINO Integrity Checker

## What is RINO Integrity Checker?


A tool for verifying RINO wallet frontend build integrity.

The tool downloads the web content served by the RINO Wallet Platform, and checks that content against the original source code of that content that RINO publishes on GitHub.

This tool allows anyone to easily check that we are serving what we say we are serving - RINO frontend code can be browsed on github, and then using this tool anyone can check that that is the same code we are serving in our web frontend.

## What does the RINO Integrity Checker do?


The RINO Integrity Checker checks three things:

1. The hash of the index.html file - this hash ensures that the entrance point to RINO is correct and the same as published on GitHub.
Thanks to your browser's built-in Subresource Integrity (SRI) implementation and content based file names,
you can be confident that as long as the index.html file is genuine, then the other resources loaded are also genuine (or at least are the same as are referenced by the genuine index.html file).

2. The hash of the service_worker.js file - this is an important file that helps ensure the integrity of various Monero sub-resources used by RINO.

3. Build hash - this hash ensures that all files used by the frontend are the same as provided by RINO.
It includes the index.html and service_worker.js content.

With these hashes matching, you can be confident that your browser is using the correct content, which you can peruse in GitHub.

The checks are done once every 15 minutes, but it can be changed in crontab file.


## How does RINO integrity checker work


The RINO integrity checker is implemented as a Docker container running a cron job that:
- Downloads the pages served by RINO web platform, and calculates relevant hashes
- Calculates hashes from the version of the code on github
- Compares the hashes and reports if there is any difference.


## How to build and run

### Local environment

1. Clone this repo and navigate to its root directory.
2. Run `mkdir -p ./output` to create the directory that output is stored in.
3. Build docker image: `docker build -t integrity-checker .`
4. Run docker container with a built image: `docker run -t -i --init -v $(pwd)/output/:/output/ integrity-checker`
5. Run `echo "$(pwd)/output/index.html"` and copy/paste the result into your browser address bar to view results...

Feel free to customise this tool to your needs
