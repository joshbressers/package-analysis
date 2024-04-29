

import requests
import urllib.parse
from requests.adapters import HTTPAdapter, Retry
from typing import List


class EcosystemsSession:
    __response: requests.Response
    __url: str
    __page_items: int
    __total_pages: int
    __total_count: int
    __data: List
    __last: str
    __first: str
    n: int

    def __init__(self, url):
        self.__response = None
        self.__url = url
        self.__page_items = 0
        self.__total_pages = 0
        self.__total_count = 0
        self.__data = []
        self.__last = False
        self.__first = None
        self.n = 0

        # Setup http session
        self.session = requests.Session()
        retries = Retry(total=10,
                        backoff_factor=1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        self.get_url()
        self.__first = self.__response.links["first"]["url"]

    def __len__(self) -> int:
        return self.__total_count

    def get_url(self) -> None:
        self.__response = self.session.get(url=self.__url)

        self.__page_items = int(self.__response.headers['page-items'])
        self.__data = self.__response.json()

        if "next" not in self.__response.links:
            # We're on the last page
            self.__last = True

    def get_next(self) -> None:
        if not self.__last:
            self.__url = self.__response.links["next"]["url"]
            self.get_url()

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n == len(self.__data):
            if not self.__last:
                self.get_next()
                self.n = 0

        if self.n < len(self.__data):
            self.n = self.n + 1
            return self.__data[self.n - 1]
        else:
            raise StopIteration

class Registry:

    def __init__(self, data):

        fields = [
            "name", "ecosystem", "packages_count", "versions_count",
            "maintainers_count", "packages_url", "maintainers_url"
        ]
        for i in fields:
            self.__dict__[i] = data[i]

    def __getitem__(self, item):
        return self.__dict__[item]

def get_registries() -> List[Registry]:
    registry_url = "https://packages.ecosyste.ms/api/v1/registries"
    session = EcosystemsSession(registry_url)

    registries = []

    for i in session:
        registries.append(Registry(i))

    return registries

class Packages:
    __session: requests.Session
    __registry: Registry
    __count: int

    def __init__(self, session, registry):
        self.__session = session
        self.__registry = registry
        self.__count = 0

        for r in get_registries():
            if r["name"] == registry:
                self.__count = int(r["packages_count"])

        self.__session_iter = iter(self.__session)

    def get_count(self) -> int:
        return self.__count

    def __iter__(self):
        return self

    def __next__(self):
        package_data = next(self.__session_iter)
        package_data["repo"] = self.__registry
        package_data["num_maintainers"] = len(package_data["maintainers"])


        # Remove some large fields
        if "metadata" in package_data: del(package_data["metadata"])
        if "repo_metadata" in package_data: del(package_data["repo_metadata"])
        if "fields" in package_data: del(package_data["fields"])

        return package_data

class Versions:

    def __init__(self, session, name, registry):
        self.__session = session
        self.__registry = registry
        self.__name = name

        self.__session_iter = iter(self.__session)

    def __iter__(self):
        return self

    def __next__(self):
        package_data = next(self.__session_iter)
        package_data["repo"] = self.__registry
        package_data["name"] = self.__name
        return package_data

def get_versions(package, registry) -> Versions:
    versions_url = f"https://packages.ecosyste.ms/api/v1/registries/{registry}/packages/{package}/versions?per_page=100"
    session = EcosystemsSession(versions_url)

    return Versions(session, package, registry)

def get_packages(registry, latest_date = "1979-01-01") -> Packages:

    latest_date = urllib.parse.quote(latest_date)
    registry_url = f"https://packages.ecosyste.ms/api/v1/registries/{registry}/packages?updated_after={latest_date}&per_page=100&sort=updated_at&order=asc"

    session = EcosystemsSession(registry_url)

    return Packages(session, registry)
