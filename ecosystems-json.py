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
from urllib.parse import urlparse

def main():

    if len(sys.argv) != 2:
        print("Usage: %s <json>" % (sys.argv[0]))
        sys.exit(1)

    json_file = sys.argv[1]
    print("Loading %s" % json_file)

    package_es = Documents('ecosystems-package', update_frequency=500, mapping='', delete=False)
    versions_es = Documents('ecosystems-versions', update_frequency=500, mapping='', delete=False)

    with open(json_file, 'r') as fp:
        #total_pages = sum(1 for line in fp)
        total_pages = 3500162
        fp.seek(0)

        current_number = 0
        progress = tqdm(total=total_pages)
        for line in fp:
            # Load package
            p_data = json.loads(line)

            new_data = {}
            new_data["repo"] = p_data["ecosystem"]
            new_data["ecosystem"] = p_data["ecosystem"]
            new_data["name"] = p_data["name"]
            new_data["normalized_licenses"] = p_data["normalized_licenses"]
            new_data["versions_count"] = p_data["versions_count"]
            new_data["latest_release_published_at"] = p_data["latest_release_published_at"]
            new_data["first_release_published_at"] = p_data["first_release_published_at"]
            new_data["dependent_packages_count"] = p_data["dependent_packages_count"]
            new_data["downloads"] = p_data["downloads"]
            new_data["rankings"] = p_data["rankings"]
            new_data["repository_url"] = p_data["repository_url"]

            try:
                the_url = urlparse(p_data["repository_url"])
                new_data["repository_name"] = the_url.hostname
            except:
                new_data["repository_name"] = ""

            doc_id = "%s-%s" % (new_data["repo"], new_data["name"])

            version_data = p_data['versions']
            error = None
            try:
                error = package_es.add(new_data, doc_id)
                if error:
                    #print(p_data)
                    logging.warning("Package")
                    logging.warn(error)
            except Exception as e:
                logging.warn("Package Output: Something bad happened")
                logging.warn(e)
                logging.warn(error)

            # Load versions
            for v in version_data:
                v["repo"] = p_data["name"]
                v["name"] = p_data["name"]
                doc_id = "%s-%s-%s" % (v["repo"], v["name"], v["number"])
                try:
                    error = versions_es.add(v, doc_id)
                    if error:
                        #print(v)
                        logging.warning("Version")
                        logging.warning(error)
                except Exception as e:
                    logging.warn("Version Output: Something bad happened")
                    logging.warn(e)
                    logging.warn(error)

            progress.n = current_number
            progress.refresh()
            current_number = current_number + 1

    progress.close()
    package_es.done()
    versions_es.done()

    print("Done Loading %s\n\n" % json_file)

if __name__ == "__main__":
    main()
