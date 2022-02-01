#! /usr/bin/env python3
"""
The sequence of operations in our yarn:build process is such that to ensure deterministic
 and sensible filenames (for cache and reproducible builds) we are left with needing this script.
 (Webpack 4 and the HashOutput/SubresourceIntegity plugins don't play well together.)

This module tackles:

* Sub Resource Integrity:

It updates the subresource-integrity hash  for`runtime-main.xxxx.js` in /build/index.html.
This is necessary because the content of `runtime-main.xxxx.js`  has been changed  by
HashOutput-plugin since its integrity hash was calculated during the build.

* Rename non-deterministic filenames

It updates `/static/css/main.xxxxxx.chunk.css` filename with a hash of its content, and
updates the link in index.html accordingly.

* Reproducible Build:

It hashes the content of each build asset and generates a  deterministic final hash from the results.
It exports './build/build-integrity.txt' containing instructions on how to reproduce this build hash.
 """
import os
import time
from datetime import datetime, timedelta
import hashlib
import pathlib
import urllib.request
from mako.template import Template


LOCAL = int(os.environ.get("LOCAL", "1"))
ENVIRON = str(os.environ.get("ENVIRON", "test"))

DOMAIN = {"test": "test.rino.io", "prod": "rino.io"}[ENVIRON]


def calculate_hash(file_path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(hasher.block_size)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest().lower()


def get_local_index_html_hash():
    path = pathlib.Path("/frontend/build/index.html")
    index_hash = calculate_hash(path)
    return index_hash


def get_integrity_hash_from_server():
    fp = urllib.request.urlopen(f"http://{DOMAIN}/build-integrity.txt")
    hash = str(fp.read()).split("\\n")[1].split(" is ")[1]
    return hash


def get_integrity_hash_from_build():
    with open("/frontend/build/build-integrity.txt", "r") as file:
        hash = str(file.read()).split("\n")[1].split(" is ")[1]
        return hash


def get_server_index_html_hash():
    fp = urllib.request.urlopen(f"http://{DOMAIN}/")
    server_index = fp.read()
    fp.close()
    hasher = hashlib.sha256(server_index)
    hash = hasher.hexdigest().lower()
    return hash


def add_db_object(integrity, ts):
    if LOCAL:
        import dbm

        with dbm.open("old_results", "c") as db:
            db[str(ts)] = integrity
    else:
        import boto3

        client = boto3.client("dynamodb", region_name="eu-west-2")
        print(ENVIRON, type(ENVIRON), ts, type(ts), integrity, type(integrity))
        client.put_item(
            TableName="IntegrityCheckTest",
            Item={
                "environ": {"S": str(ENVIRON)},
                "timestamp": {"N": str(ts)},
                "integrity": {"S": str(integrity)},
            },
        )


def get_last_results_data(n=25):
    if LOCAL:
        import dbm

        with dbm.open("old_results", flag="r", mode=438) as db:
            return [
                (
                    datetime.fromtimestamp(int(timestamp)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    db[timestamp].decode("utf-8"),
                )
                for timestamp in sorted(db.keys(), key=lambda x: -int(x))
            ]
    else:
        import boto3
        from boto3.dynamodb.conditions import Key

        client = boto3.client("dynamodb", region_name="eu-west-2")
        interval_seconds = int(os.environ.get("INTERVAL_SECONDS", 300))
        last_n_timestamp = (
            datetime.now()
            - timedelta(seconds=interval_seconds * int(n + 1 / 2))
        ).timestamp()
        response = client.query(
            KeyConditionExpression=Key("age").gt(last_n_timestamp)
        )

        return [
            (
                datetime.fromtimestamp(i["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                i["result"],
            )
            for i in sorted(response["Items"], key=lambda x: -x["timestamp"])
        ]


def write_index_file(index_html):
    if LOCAL:
        with open("/output/index.html", "w+") as file:
            file.write(index_html)
    else:
        # S3 implementation here.
        pass


if __name__ == "__main__":
    timestamp = int(time.time())
    built_index_hash = ""
    built_integrity_hash = ""
    server_index_hash = ""
    server_integrity_hash = ""

    try:
        built_index_hash = get_local_index_html_hash()
        built_integrity_hash = get_integrity_hash_from_build()
        server_index_hash = get_server_index_html_hash()
        server_integrity_hash = get_integrity_hash_from_server()

        if (
            built_index_hash != server_index_hash
            or built_integrity_hash != server_integrity_hash
        ):
            last_run_result = "FAILED"
        else:
            last_run_result = "OK"
    except Exception as e:
        print(e)
        last_run_result = "CHECK_FAILED"

    add_db_object(last_run_result, timestamp)
    old_checks_data = get_last_results_data()

    template = Template(filename="index_template.html",)
    html_string = template.render(
        **{
            "old_results": old_checks_data,
            "last_run_result": last_run_result,
            "last_run_date": datetime.fromtimestamp(timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "domain": DOMAIN,
            "build_index_hash": built_index_hash,
            "build_integrity_hash": built_integrity_hash,
            "server_index_hash": server_index_hash,
            "server_integrity_hash": server_integrity_hash,
        }
    )

    write_index_file(html_string)
