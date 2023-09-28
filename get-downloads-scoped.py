#!/usr/bin/env python

import sys
import os
import signal
import json
from pathlib import Path
import requests
import threading, queue
import time
from tqdm import tqdm

package_q = queue.Queue(maxsize=500)
results_q = queue.Queue(maxsize=500)

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
            os.kill(os.getpid(), signal.SIGINT)

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

        #print(the_file)

        results_q.task_done()

# Main
#

threading.Thread(target=put_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()
threading.Thread(target=get_worker, daemon=True).start()

with open("all_packages.json") as fh:
    data = json.load(fh)

    all_packages = data['rows']

#for filename in tqdm(all_packages, miniters=1):
for filename in all_packages:

    one_id = filename["id"]
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

    print(one_id)
    package_q.put(one_id)

while not package_q.empty():
    print("Waiting on package queue")
    time.sleep(1)

while not results_q.empty():
    print("Waiting on results queue")
    time.sleep(1)
