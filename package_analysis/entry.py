
import argparse
import package_analysis.Ecosystems
import package_analysis.Elasticsearch
from tqdm import tqdm
import threading, queue
import time
from tabulate import tabulate

# Entry points for poetry to call into

es = package_analysis.Elasticsearch.PackageAnalysisES()
version_q = queue.Queue(maxsize=1000)
lock = threading.Lock()

def cmd_repos() -> None:
    """
    List all the repos that are currently seen in Ecosyste.ms
    """
    repos = package_analysis.Ecosystems.get_registries()

    table_data = []

    for i in repos:
        table_data.append((i["name"], i["packages_count"]))

    print(tabulate(table_data, headers=["Repo", "Count"]))


def cmd_latest() -> None:
    """
    Print the latest pcakge date stored in Elasticsearch for a given registry
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=str,
        help="The registry to show the latest package date")
    args = parser.parse_args()
    registry = args.registry

    date = es.get_latest_package(registry)
    print(date)

def cmd_packages() -> None:
    """
    Load the packages for a given repo

    By default the latest date found is used at the starting point
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=str,
        help="The registry to load packages from")
    args = parser.parse_args()

    for i in range(20):
        threading.Thread(target=version_worker, args=(), daemon=True).start()

    registry = args.registry
    load_packages(registry)

def cmd_all_packages() -> None:
    "Loop over all registries and load the packages"
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="use a differnt date",
        type=str, default=None)
    args = parser.parse_args()

    for i in range(20):
        threading.Thread(target=version_worker, args=(), daemon=True).start()

    repos = package_analysis.Ecosystems.get_registries()

    for i in repos:
        registry = i["name"]
        date = es.get_latest_package(registry)
        print(f"{registry} - {date}")
        load_packages(registry, args.date)

def cmd_package_diff() -> None:
    """
    Return the different in packages stored in Elasticsearch and
    Ecosyste.ms
    """

    for i in range(20):
        threading.Thread(target=version_worker, args=(), daemon=True).start()

    repos = package_analysis.Ecosystems.get_registries()

    for r in repos:

        registry = r["name"]
        print(f"Loading Elasticsearch packages for {registry}")
        es_packages = es.get_names(registry)
        print("Done\n")
        ec_packages = package_analysis.Ecosystems.get_names(registry)

        count = 0
        for i in ec_packages:
            count = count + 1
            if not count % 10000:
                print(count)
            if i not in es_packages:
                one_package = package_analysis.Ecosystems.get_package(registry, i)
                version_q.put([one_package, registry])
                print(f"{i} {count}")

        while not version_q.empty():
            time.sleep(10)

        print("Finishing up")
        es.done()

def load_packages(registry, date) -> None:
    """
    Helper function to load the packages from a given registry

    we start at the latest date.

    TODO: Start at 1970-01-01 to load them all
    """

    if date is None:
        latest_date = es.get_latest_package(registry)
    else:
        latest_date = date
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

def version_worker() -> None:
    """
    This is the thread worker
    """

    while True:

        (package, registry) = version_q.get()
        package_name = package["name"]
        try:
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
        except:
            # Sometimes things go wrong, just put the package back in the queue
            version_q.put((package, registry))

        version_q.task_done()
