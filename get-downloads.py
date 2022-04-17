#!/usr/bin/env python

import sys
import os
import json
from pathlib import Path
import requests

file_dir = sys.argv[1]

path = Path(file_dir)
base_url = "https://api.npmjs.org/downloads/point/last-year/"

to_get = []

def get_data(package):
    # We can't do bulk requests for scoped packages, but we can for
    # everything else

    global to_get

    to_return = []

    if package.startswith('@'):
        url = base_url + package
        resp = requests.get(url=url, timeout=10)
        dl_data = resp.json()

        if "error" in dl_data:
            dl_data = {
                "downloads": -1,
                "package": package
            }

        to_return.append(dl_data)

    else:
        to_get.append(package)

        #if len(to_get) > 100:
        if len(to_get) > 1:

            url = base_url + ','.join(to_get)
            resp = requests.get(url=url, timeout=10)
            dl_data = resp.json()

            for i in dl_data.keys():

                ret_data = None

                if dl_data[i] is None:
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

for filename in path.rglob('*'):

    if os.path.isdir(filename):
        continue

    one_id = str(filename).split('/', 1)[1]
    the_file = "downloads/%s" % one_id

    if one_id.startswith('@'):
        continue

    # Things that start with a @ are special in npm
    if one_id.startswith('@'):
        (the_dir, the_package) = one_id.split('/')
        if os.path.exists("downloads/%s" % the_dir):
            # We're fine
            pass
        else:
            os.mkdir("downloads/%s" % the_dir)

    if os.path.exists(the_file):
        continue

    if one_id.startswith('@'):
        print(one_id)
    the_data = get_data(one_id)

    if len(the_data) > 0:

        for p in the_data:
            the_file = "downloads/%s" % p["package"]

            with open(the_file, "w") as fh:
                fh.write(json.dumps(p))
