#!/usr/bin/env python

import sys
import os
import gzip
import json
import vulnerabilities
from esbulkstream import Documents
from pathlib import Path

file_dir = sys.argv[1]

es = Documents('npm-packages', mapping='')
es_one = Documents('npm-one-package', mapping='')

path = Path(file_dir)

vulns = vulnerabilities.Vulnerabilities()

for filename in path.rglob('*'):

    if os.path.isdir(filename):
        continue

    one_id = str(filename).split('/', 1)[1]
    one_data = { "name": one_id }

    if one_id.startswith('@'):
        # This is a scoped package
        one_data["scoped"] = True
        (scope, name) = one_id.split('/')
        one_data["scope"] = scope
        one_data["scope_name"] = name

    with open("downloads/%s" % one_id, mode="r") as fh:
        data = json.loads(fh.read())
        if data["package"] != one_id:
            print("%s download data might be broken" % one_id)
            sys.exit(1)
        one_data["downloads"] = data["downloads"]

    with gzip.GzipFile(filename, mode="r") as fh:
        data = json.loads(fh.read())

        if "description" in data and data["description"] == "security holding package":
            one_data["security_holding"] = True

        if "name" not in data:
            print("No name %s" % filename)
            one_data["withdrawn"] = True
            es_one.add(one_data, one_id)
            continue
        if "time" not in data:
            print("No time %s" % filename)
            one_data["no_time"] = True
            es_one.add(one_data, one_id)
            continue
        package_name = data["name"]

        if "versions" in data:
            one_data["versions"] = len(data["versions"])
        elif "unpublished" in data["time"]:
            one_data["unpublished"] = True
            one_data["versions"] = len(data["time"]["unpublished"]["versions"])
        else:
            one_data["versions"] = len(data["time"])
            # The created and modified fields should always exist, but this
            # data gets pretty weird
            if one_data["versions"] > 2:
                one_data["versions"] = one_data["versions"] - 2

        one_data["vulnerabilities"] = 0

        all_vulns = []

        for ver in data["time"].keys():

            # XXX Do something with these later
            #if ver == "created":
            #    continue
            #elif ver == "modified":
            #    continue
            if ver == "unpublished":
                continue

            package_version = ver
            package_time = data["time"][ver]

            doc_id = "%s-%s" % (package_name, package_version)

            doc = {
                "name": package_name,
                "version": package_version,
                "date": package_time,
                "vulnerabilities": vulns.match(package_name, package_version)
            }

            one_data["vulnerabilities"] += len(doc["vulnerabilities"])
            all_vulns.extend(doc["vulnerabilities"])

            es.add(doc, doc_id)


        one_data["unique_vulnerabilities"] = len(set(all_vulns))
        es_one.add(one_data, one_id)


es.done()
es_one.done()
