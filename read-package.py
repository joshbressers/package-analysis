#!/usr/bin/env python

import sys
import os
import gzip
import json
from esbulkstream import Documents
from pathlib import Path

file_dir = sys.argv[1]

es = Documents('npm-packages', mapping='')

path = Path(file_dir)

for filename in path.rglob('*'):

    if os.path.isdir(filename):
        continue

    with gzip.GzipFile(filename, mode="r") as fh:
        data = json.loads(fh.read())

        if "name" not in data:
            print("No name %s" % filename)
            continue
        if "time" not in data:
            print("No time %s" % filename)
            continue
        package_name = data["name"]

        for ver in data["time"].keys():

            # XXX Do something with these later
            if ver == "created":
                continue
            elif ver == "modified":
                continue
            elif ver == "unpublished":
                continue

            package_version = ver
            package_time = data["time"][ver]

            doc_id = "%s-%s" % (package_name, package_version)

            doc = {
                "name": package_name,
                "version": package_version,
                "date": package_time
            }

            es.add(doc, doc_id)

es.done()
