#!/usr/bin/env python

import json
import requests
import gzip
import time
import os

with open("all_packages.json") as fh:
    data = json.load(fh)

    all_packages = data['rows']
    all_packages.reverse()

    for package_data in all_packages:

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

        print(package_name)
        resp = requests.get(url=url, timeout=10)
        npm_data = resp.json()

        with gzip.GzipFile(filename, mode="w") as outfh:
            outfh.write(str.encode(json.dumps(npm_data)))

