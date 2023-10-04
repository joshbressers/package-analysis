#!/usr/bin/env python

import json
import requests
from requests.adapters import HTTPAdapter, Retry
from esbulkstream import Documents
from tqdm import tqdm
import threading, queue
import time
import logging
import sys

class Registry:

    def __init__(self, registry_name):
        self.name = registry_name
        self.url = "https://packages.ecosyste.ms/api/v1/registries/%s" % (registry_name)

        # Setup http session
        self.session = requests.Session()
        retries = Retry(total=25,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        self.packages_count = None

    def get_packages_count(self):
        if self.packages_count is None:
            resp = self.session.get(url=self.url, timeout=30)
            self.packages_count = int(resp.json()["packages_count"])
        return self.packages_count

    def get_num_pages(self):
        # The pages start at 1, so add one
        return int((self.get_packages_count() / 100) + 1)




# Setup URL things
package_url = "https://packages.ecosyste.ms/api/v1/registries/%s/packages?page=%d&per_page=100&sort=name"
version_url = "https://packages.ecosyste.ms/api/v1/registries/%s/packages/%s/versions?page=1&per_page=100"


page_q = queue.Queue()
package_output_q = queue.Queue(maxsize=3000)
version_output_q = queue.Queue(maxsize=3000)
version_q = queue.Queue(maxsize=3000)

package_es = Documents('ecosystems-package', mapping='', delete=False)
versions_es = Documents('ecosystems-versions', mapping='', delete=False)

def version_worker(repo):
    # Setup http session
    s = requests.Session()
    retries = Retry(total=25,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    while True:
        package = version_q.get()

        new_url = version_url % (repo, package)
        my_data = []
        try:
            response = s.get(url=new_url)
            version_json = response.json()
            for i in version_json:
                i["repo"] = repo
                my_data.append(i)

            while response.links.get('next'):
                response = s.get(response.links['next']['url'])
                version_json = response.json()
                for i in version_json:
                    i["repo"] = repo
                    my_data.append(i)

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


def package_worker(repo):
    # Setup http session
    s = requests.Session()
#    retries = Retry(total=500,
#                    backoff_factor=0.1,
#                    status_forcelist=[ 500, 502, 503, 504 ])
#    s.mount('https://', HTTPAdapter(max_retries=retries))

    while True:
        page = page_q.get()

        new_url = package_url % (repo, page)
        try:
            resp = s.get(url=new_url)
            package_json = resp.json()


            for p in package_json:

                version_q.put(p["name"])

                p["repo"] = repo
                p["num_maintainers"] = len(p["maintainers"])

                package_output_q.put(p)

        except:
            # If something bad happens, just put the page back in the queue
            logging.warn("Package: Something bad happened")
            page_q.put(page)

        page_q.task_done()

def package_output_worker():
    while True:
        result = package_output_q.get()
        doc_id = "%s-%s" % (result["repo"], result["name"])
        package_es.add(result, doc_id)
        package_output_q.task_done()

def version_output_worker():
    while True:
        result = version_output_q.get()
        doc_id = "%s-%s-%s" % (result["repo"], result["name"], result["number"])
        versions_es.add(result, doc_id)
        version_output_q.task_done()

def main():

    if len(sys.argv) != 2:
        print("Usage: %s <repo>" % (sys.argv[0]))
        sys.exit(1)

    repo_name = sys.argv[1]

    my_repo = Registry(repo_name)
    total_pages = my_repo.get_num_pages()

    for page in range(1, total_pages + 1):
        page_q.put(page)

    threading.Thread(target=package_output_worker, daemon=True).start()
    threading.Thread(target=version_output_worker, daemon=True).start()

    for i in range(15):
        threading.Thread(target=version_worker, args=(repo_name,), daemon=True).start()
    for i in range(2):
        threading.Thread(target=package_worker, args=(repo_name,), daemon=True).start()

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
