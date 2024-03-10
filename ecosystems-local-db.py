#!/usr/bin/env python

import json
import requests
from requests.adapters import HTTPAdapter, Retry
from esbulkstream import Documents
from tqdm import tqdm
import threading, queue
import time
import psycopg2

conn = psycopg2.connect(database = "packages_production",
                        user = "postgres",
                        host = 'localhost',
                        password = 'password',
                        port = 5432)


package_output_q = queue.Queue(maxsize=1000)
version_output_q = queue.Queue(maxsize=1000)

package_es = Documents('npm-package-ecosystems', mapping='', delete=True)
versions_es = Documents('npm-versions-ecosystems', mapping='', delete=True)


def package_output_worker():
    while True:
        result = package_output_q.get()
        doc_id = "%s-%s" % (result["name"], result["ecosystem"])
        package_es.add(result, doc_id)
        package_output_q.task_done()

def version_output_worker():
    while True:
        result = version_output_q.get()
        doc_id = "%s-%s" % (result["package_id"], result["number"])
        versions_es.add(result, doc_id)
        version_output_q.task_done()

def get_packages_number():
    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM packages;')
    rows = cur.fetchone()
    return rows[0]

def get_versions(id, name, registry):
    cur = conn.cursor()
    cur.execute('select id,package_id,number,published_at,licenses,integrity,status,created_at,updated_at,metadata from versions where package_id = %d' % id)
    the_records = cur.fetchall()
    for record in the_records:
        my_data = {}
        my_data["id"] = record[0]
        my_data["package_id"] = record[1]
        my_data["number"] = record[2]
        if record[3] is not None:
            my_data["published_at"] = record[3].isoformat()
        else:
            my_data["published_at"] = None
        my_data["licenses"] = record[4]
        my_data["integrity"] = record[5]
        my_data["status"] = record[6]

        if record[7] is not None:
            my_data["created_at"] = record[7].isoformat()
        else:
            my_data["created_at"] = None

        if record[8] is not None:
            my_data["updated_at"] = record[8].isoformat()
        else:
            my_data["updated_at"] = None

        #my_data["metadata"] = record[9]
        my_data["package"] = name
        my_data["registry"] = registry

        version_output_q.put(my_data)

def main():

    num_packages = get_packages_number()

    threading.Thread(target=package_output_worker, daemon=True).start()
    threading.Thread(target=version_output_worker, daemon=True).start()

    progress = tqdm(total=num_packages)

    cur = conn.cursor("packages_cursor")
    cur.itersize = 1000
    cur.execute('select name,ecosystem,normalized_licenses,versions_count,first_release_published_at,latest_release_published_at,dependent_packages_count,rankings,advisories,downloads,downloads_period,maintainers_count,id from packages')
    while True:
        the_records = cur.fetchmany()
        if not the_records:
            break
        for record in the_records:

            get_versions(record[-1], record[0], record[1])

            my_data = {}
            my_data["name"] = record[0]
            my_data["ecosystem"] = record[1]
            my_data["normalized_licenses"] = record[2]
            my_data["versions_count"] = record[3]
            if record[4] is not None:
                my_data["first_release_published_at"] = record[4].isoformat()
            else:
                my_data["first_release_published_at"] = None

            if record[5] is not None:
                my_data["latest_release_published_at"] = record[5].isoformat()
            else:
                my_data["latest_release_published_at"] = None

            my_data["dependent_packages_count"] = record[6]
            my_data["rankings"] = record[7]
            my_data["advisories"] = record[8]
            my_data["downloads"] = record[9]
            my_data["downloads_period"] = record[10]
            my_data["maintainers"] = record[11]

            package_output_q.put(my_data)

            progress.n = progress.n + 1
            progress.refresh()

    while not package_output_q.empty():
        pass # Do nothing

    while not version_output_q.empty():
        pass # Do nothing

    package_es.done()
    versions_es.done()

    progress.close()

if __name__ == "__main__":
    main()
