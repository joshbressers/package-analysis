#!/usr/bin/env python

import json
import requests
import gzip
import time
import os
from tqdm import tqdm

with open("all_packages.json") as fh:
    data = json.load(fh)

    all_packages = data['rows']
    all_packages.reverse()

    # give the status bar some room
    print("\n\n\n")
    for package_data in tqdm(all_packages, miniters=1):

        package_name = package_data['id']
        filename = "output/%s" % package_name
        url = 'https://registry.npmjs.org/%s' % package_name

        # Things that start with a @ are special in npm
        if package_name.startswith('@'):
            (the_dir, the_package) = package_name.split('/')
            if os.path.exists("output/%s" % the_dir):
                # We're fine
                pass
            else:
                os.mkdir("output/%s" % the_dir)

        if os.path.exists(filename):
            continue

        #print(package_name)
        resp = requests.get(url=url, timeout=30)
        npm_data = resp.json()

        with open(filename, mode="w") as outfh:
            outfh.write(json.dumps(npm_data))

