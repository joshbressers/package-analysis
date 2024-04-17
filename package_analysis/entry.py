
import argparse
import package_analysis.Ecosystems

def repos():
    package_analysis.Ecosystems.get_registries()

def packages():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=str,
        help="The registry to load packages from")
    args = parser.parse_args()
    registry = args.registry
    package_analysis.Ecosystems.get_packages(registry)
