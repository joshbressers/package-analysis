import json
import os
import requests

from io import BytesIO
from typing import Any, List, Mapping
from zipfile import ZipFile
from version_parser import Version

def get_packages_to_vulns() -> Mapping[str, Any]:
    npm_zip = ZipFile(BytesIO(requests.get('https://osv-vulnerabilities.storage.googleapis.com/npm/all.zip').content))
    package_to_vulns = {}

    for advisory_path in npm_zip.namelist():
        advisory = json.loads(npm_zip.read(advisory_path))

        for affected in advisory.get("affected", []):
            package_name = affected.get("package", {}).get("name")

            if not package_name:
                continue

            if package_name not in package_to_vulns:
                package_to_vulns[package_name] = []

            package_to_vulns[package_name].append(advisory)

    return package_to_vulns

class Vulnerabilities:
    def __init__(self):
        self.packages_to_vulns = get_packages_to_vulns() 

    def match(self, package_name: str, package_version: str) -> List[str]:
        if package_name not in self.packages_to_vulns:
            return []

        vulns = []

        try:
            parsed_package_version = Version(package_version)
        except:
            # Skip weird versions, they won't match any vulns anyway
            return []

        for vuln in self.packages_to_vulns[package_name]:
            for affected in vuln["affected"]:
                package = affected["package"]["name"]

                if package_name != package:
                    continue

                for r in affected.get("ranges", []):
                    if r.get("type") != "SEMVER":
                        continue

                    matched = False

                    try:
                        for event in r.get("events", []):
                            if event.get("introduced") and parsed_package_version >= Version(event.get("introduced")):
                                matched = True
                                continue

                            if matched and event.get("fixed") and parsed_package_version < Version(event.get("fixed")):
                                break
                            else:
                                matched = False

                        if matched:
                            vulns.append(vuln["id"])
                            break
                    except:
                        # Sometimes version things fail
                        break

        return vulns
                            

