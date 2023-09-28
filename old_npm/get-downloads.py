#!/usr/bin/env python

import sys
import os
import json
from pathlib import Path
import requests

base_url = "https://api.npmjs.org/downloads/point/last-year/"

to_get = []

def get_data(package):
    # We can't do bulk requests for scoped packages, but we can for
    # everything else

    global to_get

    print(package)

    to_return = []

    # Skip the scoped packages
    #if package.startswith('@'):
    #    return
    #else:
    if True:
        to_get.append(package)

        if len(to_get) > 100:
        #if len(to_get) > 0:

            url = base_url + ','.join(to_get)
            resp = requests.get(url=url, timeout=10)
            dl_data = resp.json()

            # If we only requested one thing, it's a very different result
            if len(to_get) == 1:
                ret_data = None

                if "error" in dl_data:
                    ret_data = {
                        "downloads": -1,
                        "package": package
                    }
                else:
                    ret_data = dl_data

                    to_return.append(ret_data)

            # We requested multiple things
            else:

                for i in dl_data.keys():

                    ret_data = None

                    if dl_data[i] is None:
                        ret_data = {
                            "downloads": -1,
                            "package": i
                        }
                    elif f"package {package} not found" in dl_data[i]:
                        ret_data = {
                            "downloads": -1,
                            "package": package
                        }
                    else:
                        ret_data = dl_data[i]

                    to_return.append(ret_data)

            # Don't forget to clear to_get
            to_get = []

    return to_return


with open("all_packages.json") as fh:
    data = json.load(fh)

    all_packages = data['rows']

for filename in all_packages:

    package_name = filename["id"]
    the_file = "downloads/%s" % package_name

    # Things that start with a @ are special in npm
    if package_name.startswith('@'):
        (the_dir, the_package) = package_name.split('/')
        if os.path.exists("downloads/%s" % the_dir):
            # We're fine
            pass
        else:
            os.mkdir("downloads/%s" % the_dir)

    if os.path.exists(the_file):
        continue

    if package_name.startswith('@'):
        print(package_name)
    the_data = get_data(package_name)

    if len(the_data) > 0:

        for p in the_data:
            the_file = "downloads/%s" % p["package"]

            with open(the_file, "w") as fh:
                fh.write(json.dumps(p))
