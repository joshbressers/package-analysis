#!/usr/bin/env python

import sys
import os
import gzip
import json
import regex
import vulnerabilities
from esbulkstream import Documents
from pathlib import Path

file_dir = sys.argv[1]

version_re = regex.compile(r"\d+\.\d+\.\d+")

es = Documents('npm-versions', mapping='')

path = Path(file_dir)

vulns = vulnerabilities.Vulnerabilities()

for filename in path.rglob('*'):

    if os.path.isdir(filename):
        continue

    with gzip.GzipFile(filename, mode="r") as fh:
        data = json.loads(fh.read())

        if "name" not in data:
            #print("No name %s" % filename)
            continue
        package_name = data["name"]

        if not "versions" in data:
            # These are unpublished packages. Maybe do something with this
            # later
            continue

        num_versions = len(data["versions"].keys())

        if "latest" in data["dist-tags"]:
            latest_ver = data["dist-tags"]["latest"]
        else:
            print("No latest %s" % filename)
            latest_ver = None

        for ver in data["versions"].keys():

            is_latest = False
            if ver == latest_ver:
                is_latest = True

            dep_array = []

            package_version = ver

            num_maintainers = -1
            if "maintainers" in data["versions"][ver]:
                num_maintainers = len(data["versions"][ver]["maintainers"])

            size = -1
            if "unpackedSize" in data["versions"][ver]["dist"]:
                size = data["versions"][ver]["dist"]["unpackedSize"]

            if "dependencies" in data["versions"][ver]:
                if type(data["versions"][ver]["dependencies"]) is list:
                    print("List: %s" % filename)
                    continue

                if type(data["versions"][ver]["dependencies"]) is str:
                    print("String: %s" % filename)
                    continue

                if type(data["versions"][ver]["dependencies"]) is type(None):
                    print("None: %s" % filename)
                    continue


                for dep in data["versions"][ver]["dependencies"].keys():

                    if data["versions"][ver]["dependencies"][dep] == "":
                        continue

                    if data["versions"][ver]["dependencies"][dep] is None:
                        continue

                    if type(data["versions"][ver]["dependencies"][dep]) is dict:
                        # There are few of these (3 to be exact) and the
                        # dependency dict is a mess. Let's just skip them
                        continue

                    # Now we need to build a npm version parser
                    dep_name = dep
                    dep_ver = data["versions"][ver]["dependencies"][dep]

                    # The npm semver spec is REALLY large. We need to start
                    # small

                    # Let's detect the operation type in the version
                    # ^ ~
                    dep_ops = []

                    if '^' in dep_ver:
                        dep_ops.append("^")
                    if '~' in dep_ver:
                        dep_ops.append("~")
                    if '*' in dep_ver:
                        dep_ops.append("*")
                    if ">" in dep_ver:
                        dep_ops.append(">")
                    if "<" in dep_ver:
                        dep_ops.append("<")
                    if "=" in dep_ver:
                        dep_ops.append("=")
                    if "<=" in dep_ver:
                        dep_ops.append("<=")
                    if ">=" in dep_ver:
                        dep_ops.append(">=")

                    dep_data = {
                        "dep_name" : dep_name,
                        "dep_ops"  : dep_ops
                    }
                    dep_array.append(dep_data)


            doc_id = "%s-%s" % (package_name, package_version)

            doc = {
                "name": package_name,
                "version": package_version,
                "num_maintainers": num_maintainers,
                "size": size,
                "dependencies": dep_array,
                "num_deps" : len(dep_array),
                "is_latest": is_latest,
                "vulnerabilities": vulns.match(package_name, package_version)
            }

            es.add(doc, doc_id)

es.done()
