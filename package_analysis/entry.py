
import argparse
import package_analysis.Ecosystems
import package_analysis.Elasticsearch
from tqdm import tqdm
import threading, queue
import time
from tabulate import tabulate

version_q = queue.Queue(maxsize=1000)
package_data = {}
es = package_analysis.Elasticsearch.PackageAnalysisES()
lock = threading.Lock()

def repos():
    repos = package_analysis.Ecosystems.get_registries()

    table_data = []

    for i in repos:
        table_data.append((i["name"], i["packages_count"]))

    print(tabulate(table_data, headers=["Repo", "Count"]))


def latest():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=str,
        help="The registry to show the latest package date")
    args = parser.parse_args()
    registry = args.registry

    date = es.get_latest_package(registry)
    print(date)

def packages():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=str,
        help="The registry to load packages from")
    args = parser.parse_args()


    registry = args.registry

    latest_date = es.get_latest_package(registry)
    packages = package_analysis.Ecosystems.get_packages(registry, latest_date)

    total_packages = packages.get_count()
    progress = tqdm(total=total_packages)

    for i in range(20):
        threading.Thread(target=version_worker, args=(), daemon=True).start()

    count = 0
    for i in packages:
        package_name = i["name"]
        lock.acquire()
        package_data[package_name] = i
        lock.release()
        version_q.put([package_name, registry])
        progress.n = count
        progress.refresh()
        count = count + 1

    while not version_q.empty():
        pass # Do nothing

    lock.acquire()

    # Clean up any leftover package data
    for key in package_data:
        es.add_package(package_data[key])

    lock.release()

    progress.close()
    es.done()

def version_worker():

    while True:

        (package, registry) = version_q.get()
        for p in package_analysis.Ecosystems.get_versions(package, registry):
            lock.acquire()
            es.add_version(p)
            lock.release()

        # Only add the package data after the version data is added. This
        # avoids a situation where we've added package data but not version
        # data
        lock.acquire()
        if package in package_data:
            es.add_package(package_data[package])
            del(package_data[package])
        lock.release()

        version_q.task_done()
