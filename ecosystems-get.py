#!/usr/bin/env python

import json
import requests
from requests.adapters import HTTPAdapter, Retry
from esbulkstream import Documents
from tqdm import tqdm
import threading, queue
import time
import logging


# Setup URL things
npm_url = "https://packages.ecosyste.ms/api/v1/registries/npmjs.org"
package_url = "https://packages.ecosyste.ms/api/v1/registries/npmjs.org/packages?page=%d&per_page=100&sort=name"
version_url = "https://packages.ecosyste.ms/api/v1/registries/npmjs.org/packages/%s/versions?page=1&per_page=100"

s = requests.Session()

retries = Retry(total=500,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])

s.mount('https://', HTTPAdapter(max_retries=retries))


page_q = queue.Queue()
package_output_q = queue.Queue(maxsize=3000)
version_output_q = queue.Queue(maxsize=3000)
version_q = queue.Queue(maxsize=3000)

package_es = Documents('npm-package-ecosystems', mapping='', delete=True)
versions_es = Documents('npm-versions-ecosystems', mapping='', delete=True)

def version_worker():

    while True:
        package = version_q.get()

        new_url = version_url % (package)
        my_data = []
        try:
            response = s.get(url=new_url)
            version_json = response.json()

            my_data.extend(version_json)

            while response.links.get('next'):
                response = s.get(response.links['next']['url'])
                my_data.extend(response.json())

        except:
            # If something bad happens, just put the page back in the queue
            logging.warning("Version: Something bad happened")
            version_q.put(package)
        else:
            for p in my_data:
                p["name"] = package
                version_output_q.put(p)

        # Only write this if everything worked
        version_q.task_done()


def rest_worker():
    while True:
        page = page_q.get()

        new_url = package_url % (page)
        try:
            resp = s.get(url=new_url)
            package_json = resp.json()


            for p in package_json:

                version_q.put(p["name"])

                my_data = {}
                my_data["name"] = p["name"]
                my_data["ecosystem"] = p["ecosystem"]
                my_data["normalized_licenses"] = p["normalized_licenses"]
                my_data["versions_count"] = p["versions_count"]
                my_data["first_release_published_at"] = p["first_release_published_at"]
                my_data["latest_release_published_at"] = p["latest_release_published_at"]
                my_data["dependent_packages_count"] = p["dependent_packages_count"]
                my_data["rankings"] = p["rankings"]
                my_data["advisories"] = p["advisories"]
                my_data["downloads"] = p["downloads"]
                my_data["downloads_period"] = p["downloads_period"]
                my_data["maintainers"] = p["maintainers"]
                my_data["num_maintainers"] = len(p["maintainers"])

                package_output_q.put(my_data)

        except:
            # If something bad happens, just put the page back in the queue
            logging.warn("Version: Something bad happened")
            page_q.put(page)

        page_q.task_done()

def package_output_worker():
    while True:
        result = package_output_q.get()
        doc_id = result["name"]
        package_es.add(result, doc_id)
        package_output_q.task_done()

def version_output_worker():
    while True:
        result = version_output_q.get()
        doc_id = "%s-%s" % (result["name"], result["number"])
        versions_es.add(result, doc_id)
        version_output_q.task_done()

def get_packages_number():
    resp = s.get(url=npm_url, timeout=30)
    return resp.json()["packages_count"]

def main():

    num_packages = get_packages_number()
    # The pages start at 1, so add one
    total_pages = int((num_packages / 100) + 1)
    for page in range(1, total_pages + 1):
        page_q.put(page)

    threading.Thread(target=package_output_worker, daemon=True).start()
    threading.Thread(target=version_output_worker, daemon=True).start()
    for i in range(15):
        threading.Thread(target=version_worker, daemon=True).start()
    for i in range(10):
        threading.Thread(target=rest_worker, daemon=True).start()

    progress = tqdm(total=total_pages)

    while not page_q.empty():
        time.sleep(1)
        number_left = total_pages - page_q.qsize()
        progress.n = number_left
        progress.refresh()
    progress.close()

    while not package_output_q.empty():
        pass # Do nothing

    while not version_output_q.empty():
        pass # Do nothing

    package_es.done()
    versions_es.done()

if __name__ == "__main__":
    main()
