
import argparse
import package_analysis.Ecosystems
import package_analysis.Elasticsearch
from tqdm import tqdm

def repos():
    repos = package_analysis.Ecosystems.get_registries()

    print(f'Registry\t\tPackages')
    for i in repos:
        print(f'{i["name"]}\t\t{i["packages_count"]}')

def packages():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=str,
        help="The registry to load packages from")
    args = parser.parse_args()


    registry = args.registry
    packages = package_analysis.Ecosystems.get_packages(registry)

    total_packages = packages.get_count()
    progress = tqdm(total=total_packages)

    es = package_analysis.Elasticsearch.PackageAnalysisES()

    count = 0
    for i in packages:
        es.add_package(i)
        progress.n = count
        progress.refresh()
        count = count + 1


    progress.close()
    es.done()
