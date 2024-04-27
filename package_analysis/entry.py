
import argparse
import package_analysis.Ecosystems
import package_analysis.Elasticsearch
from tqdm import tqdm
import threading, queue
import time
from tabulate import tabulate

version_q = queue.Queue(maxsize=1000)
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

    for i in range(20):
        threading.Thread(target=version_worker, args=(), daemon=True).start()

    registry = args.registry
    load_packages(registry)

def all_packages():
    "Loop over all registries and load the packages"

    for i in range(20):
        threading.Thread(target=version_worker, args=(), daemon=True).start()

    repos = package_analysis.Ecosystems.get_registries()

    for i in repos:
        registry = i["name"]
        print(registry)
        load_packages(registry)

def load_packages(registry):

    latest_date = es.get_latest_package(registry)
    packages = package_analysis.Ecosystems.get_packages(registry, latest_date)

    total_packages = packages.get_count()
    progress = tqdm(total=total_packages, ncols=70)

    count = 0
    for i in packages:
        version_q.put([i, registry])
        progress.n = count
        progress.refresh()
        count = count + 1

    while not version_q.empty():
        time.sleep(10)

    progress.close()
    print("Finishing up")
    es.done()

def version_worker():

    while True:

        (package, registry) = version_q.get()
        package_name = package["name"]
        for p in package_analysis.Ecosystems.get_versions(package_name, registry):
            lock.acquire()
            es.add_version(p)
            lock.release()

        # Only add the package data after the version data is added. This
        # avoids a situation where we've added package data but not version
        # data
        lock.acquire()
        es.add_package(package)
        lock.release()

        version_q.task_done()
