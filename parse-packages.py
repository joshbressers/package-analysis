#!/usr/bin/env python

import json
import requests
import gzip
import time

with open("all_packages.json") as fh:
    data = json.load(fh)

    for package_data in data['rows']:

        package_name = package_data['id']
        url = 'https://registry.npmjs.org/%s' % package_name

        print(package_name)
        resp = requests.get(url=url)
        npm_data = resp.json()

        with gzip.GzipFile("output/%s" % package_name, mode="w") as outfh:
            outfh.write(str.encode(json.dumps(npm_data)))

        time.sleep(1)
