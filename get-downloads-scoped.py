#!/usr/bin/env python

import sys
import os
import json
from pathlib import Path
import requests
import threading, queue

package_q = queue.Queue(maxsize=3000)
results_q = queue.Queue(maxsize=3000)

file_dir = sys.argv[1]

path = Path(file_dir)
base_url = "https://api.npmjs.org/downloads/point/last-year/"

to_get = []

def get_worker():
    # We can't do bulk requests for scoped packages, but we can for
    # everything else

    while True:

        package = package_q.get()

        url = base_url + package
        try:
            resp = requests.get(url=url, timeout=10)
        except:
            # Lots of weird things happen when this times out in a thread,
            # this is the lazy solution
            sys.exit(1)

        dl_data = resp.json()

        if "error" in dl_data:
            dl_data = {
                "downloads": -1,
                "package": package
            }

        results_q.put(dl_data)
        package_q.task_done()

def put_worker():

    while True:
        result = results_q.get()

        package = result["package"]

        the_file = "downloads/%s" % package

        with open(the_file, "w") as fh:
            fh.write(json.dumps(result))

        print(the_file)

        results_q.task_done()

# Main
#

threading.Thread(target=put_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()

for filename in path.rglob('*'):

    if os.path.isdir(filename):
        continue

    one_id = str(filename).split('/', 1)[1]
    the_file = "downloads/%s" % one_id

    # We only want scoped things
    if not one_id.startswith('@'):
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

    package_q.put(one_id)

while not package_q.empty():
    time.sleep(1)

while not results_q.empty():
    time.sleep(1)
