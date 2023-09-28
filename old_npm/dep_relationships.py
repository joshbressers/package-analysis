#!/usr/bin/env python

import sys
import os
import json
import regex
import vulnerabilities
from esbulkstream import Documents
from pathlib import Path
from tqdm import tqdm
from version_parser import Version

def get_deps(file_dir):

    path = Path(file_dir)

    dep_graph = {}

    file_count = 0
    for i in path.rglob('*'):
        file_count += 1

    for filename in tqdm(path.rglob('*'), total=file_count):

        if os.path.isdir(filename):
            continue

        with open(filename, mode="r") as fh:
            data = json.loads(fh.read())

            if "name" not in data:
                #print("No name %s" % filename)
                continue

            package_name = data["name"]

            if package_name not in dep_graph:
                dep_graph[package_name] = 0

            if not "versions" in data:
                # These are unpublished packages. Maybe do something with this
                # later
                continue

            for ver in data["versions"].keys():
                dep_set = set()

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

                        dep_set.add(dep)

                    # We only want to count a dep reference once per package.
                    # Otherwise a package with A LOT of releases could skew the
                    # numbers
                    for i in dep_set:
                        if i not in dep_graph:
                            dep_graph[i] = 0
                        dep_graph[i] += 1

    return dep_graph


def get_vers(file_dir):

    path = Path(file_dir)

    the_vers = {}

    file_count = 0
    for i in path.rglob('*'):
        file_count += 1

    for filename in tqdm(path.rglob('*'), total=file_count):

        if os.path.isdir(filename):
            continue

        with open(filename, mode="r") as fh:
            data = json.loads(fh.read())

            if "name" not in data:
                #print("No name %s" % filename)
                continue

            package_name = data["name"]

            if package_name not in the_vers:
                the_vers[package_name] = {}

            if not "time" in data:
                # These are unpublished packages. Maybe do something with this
                # later
                continue

            for ver in data["time"].keys():

                if ver == "modified":
                    continue
                elif ver == "created":
                    continue

                one_ver = Version(ver)

                # Skip weird versions
                #if type(one_ver) is LegacyVersion:
                #    continue

                the_time = data["time"][ver]

                major = one_ver.get_major_version()
                minor = one_ver.get_minor_version()
                micro = one_ver.get_micro_version()

                if not major in the_vers[package_name]:
                    the_vers[package_name][major] = {}

                if not minor in the_vers[package_name][major]:
                    the_vers[package_name][major][minor] = {}

                if not micro in the_vers[package_name][major][minor]:
                    the_vers[package_name][major][minor][micro] = the_time

    return dep_graph
