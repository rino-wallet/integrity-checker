#! /usr/bin/env python3
"""
This script compares hashes created by the local build ('check_hash.sh') against hashes from RINO's website.

1. The hash of the entire build contents
2. The root index.html file hash
3. The service_worker.js file hash
 """
import os
import time
from datetime import datetime, timedelta
import hashlib
import pathlib
import urllib.request
import dbm

from mako.template import Template


RINO_ENVIRON = str(os.environ.get("RINO_ENVIRON", "test"))
DOMAIN = {"test": "app.test.rino.io", "master": "app.rino.io"}[RINO_ENVIRON]


class CheckerResult:
    MATCH = "MATCH"
    NOT_MATCH = "NOT_MATCH"
    CHECK_FAILED = "CHECK_FAILED"


def calculate_hash_from_path(file_path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(hasher.block_size)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest().lower()


def get_local_file_hash(filename):
    path = pathlib.Path(f"/frontend/build/{filename}")
    hash = calculate_hash_from_path(path)
    return hash


def get_integrity_hash_from_server():
    with urllib.request.urlopen(f"https://{DOMAIN}/build-integrity.txt") as fp:
        hash = str(fp.read()).split("\\n")[1].split(" is ")[1]
        return hash


def get_integrity_hash_from_build():
    with open("/frontend/build/build-integrity.txt", "r") as file:
        hash = str(file.read()).split("\n")[1].split(" is ")[1]
        return hash


def get_server_file_hash(path):
    fp = urllib.request.urlopen(f"https://{DOMAIN}/{path}")
    server_index = fp.read()
    fp.close()
    hasher = hashlib.sha256(server_index)
    hash = hasher.hexdigest().lower()
    return hash


def add_db_object(integrity, ts):
    with dbm.open("old_results", "c") as db:
            db[str(ts)] = integrity


def get_last_results_data(n=25):
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


def write_index_file(index_html):
    with open("/output/index.html", "w+") as f:
        f.write(index_html)


if __name__ == "__main__":
    timestamp = int(time.time())

    built_index_hash = ""
    built_integrity_hash = ""
    built_worker_hash = ""

    server_index_hash = ""
    server_integrity_hash = ""
    server_worker_hash = ""

    try:
        built_index_hash = get_local_file_hash("index.html")
        server_index_hash = get_server_file_hash("")

        built_integrity_hash = get_integrity_hash_from_build()
        server_integrity_hash = get_integrity_hash_from_server()

        built_worker_hash = get_local_file_hash("service_worker.js")
        server_worker_hash = get_server_file_hash("service_worker.js")

        if (
            built_index_hash == server_index_hash
            and built_integrity_hash == server_integrity_hash
            and built_worker_hash == server_worker_hash
        ):
            current_run_result = CheckerResult.MATCH
        else:
            current_run_result = CheckerResult.NOT_MATCH
    except Exception as e:
        print(f"Check Failed due to an Exception...\n{e}")
        current_run_result = CheckerResult.CHECK_FAILED

    add_db_object(current_run_result, timestamp)
    old_checks_data = get_last_results_data()

    template = Template(
        filename="index_template.html",
    )
    html_string = template.render(
        **{
            "old_results": old_checks_data,
            "current_run_result": current_run_result,
            "current_run_date": datetime.fromtimestamp(timestamp).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "domain": DOMAIN,
            "build_index_hash": built_index_hash,
            "build_integrity_hash": built_integrity_hash,
            "build_worker_hash": built_worker_hash,
            "server_index_hash": server_index_hash,
            "server_integrity_hash": server_integrity_hash,
            "server_worker_hash": server_worker_hash,
        }
    )

    write_index_file(html_string)
