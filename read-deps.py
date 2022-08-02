#!/usr/bin/env python

import sys
import os
import json
import regex
import vulnerabilities
from esbulkstream import Documents
from pathlib import Path
from tqdm import tqdm

file_dir = sys.argv[1]

version_re = regex.compile(r"\d+\.\d+\.\d+")

es = Documents('npm-versions', mapping='', delete=True)

path = Path(file_dir)

vulns = vulnerabilities.Vulnerabilities()

progress_bar = tqdm(total=2174520)
for filename in path.rglob('*'):
    progress_bar.update()

    if os.path.isdir(filename):
        continue

    one_id = str(filename).split('/', 1)[1]
    downloads = 0
    with open("downloads/%s" % one_id, mode="r") as fh:
        try:
            data = json.loads(fh.read())
        except:
            progress_bar.close()
            print("\n*** Failed to read downloads/%s\n" % one_id)
            sys.exit(1)
        if data["package"] != one_id:
            progress_bar.close()
            print("\n*** %s download data might be broken\n" % one_id)
            sys.exit(1)
        downloads = data["downloads"]

    with open(filename, mode="r") as fh:
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
            #print("No latest %s" % filename)
            latest_ver = None

        for ver in data["versions"].keys():

            is_latest = False
            if ver == latest_ver:
                is_latest = True

            dep_array = []

            maintainers = []
            maintainers_email = []
            maintainer_domain = []
            if "maintainers" in data["versions"][ver]:
                for m in data["versions"][ver]["maintainers"]:
                    if type(m) is dict:
                        if "email" in m:
                            maintainers_email.append(m["email"])
                            if len(m["email"].split('@')) == 2:
                                maintainer_domain.append(m["email"].split('@')[1])
                        if "name" in m:
                            maintainers.append(m["name"])

            package_version = ver

            num_maintainers = -1
            if "maintainers" in data["versions"][ver]:
                num_maintainers = len(data["versions"][ver]["maintainers"])

            size = -1
            if "unpackedSize" in data["versions"][ver]["dist"]:
                size = data["versions"][ver]["dist"]["unpackedSize"]

            if "dependencies" in data["versions"][ver]:
                if type(data["versions"][ver]["dependencies"]) is list:
                    #print("List: %s" % filename)
                    continue

                if type(data["versions"][ver]["dependencies"]) is str:
                    #print("String: %s" % filename)
                    continue

                if type(data["versions"][ver]["dependencies"]) is type(None):
                    #print("None: %s" % filename)
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

                    if len(dep_ops) == 0:
                        dep_ops.append("none")

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
                "maintainers": maintainers,
                "maintainers_email": maintainers_email,
                "maintainer_domain": maintainer_domain,
                "size": size,
                "dependencies": dep_array,
                "num_deps" : len(dep_array),
                "is_latest": is_latest,
                "downloads" : downloads,
                "vulnerabilities": vulns.match(package_name, package_version)
            }

            es.add(doc, doc_id)

es.done()
