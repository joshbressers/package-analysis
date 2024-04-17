

import requests
from requests.adapters import HTTPAdapter, Retry

class EcosystemsSession:

    def __init__(self, url):
        self.__response = None
        self.__url = url
        self.__current_page = 0
        self.__page_items = 0
        self.__total_pages = 0
        self.__total_count = 0
        self.__data = []
        self.__last = False
        self.__first = None

        # Setup http session
        self.session = requests.Session()
        retries = Retry(total=10,
                        backoff_factor=1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        self.get_url()
        self.__first = self.__response.links["first"]["url"]

    def __len__(self):
        return self.__total_count

    def get_url(self):
        self.__response = self.session.get(url=self.__url)

        self.__current_page = int(self.__response.headers['current-page'])
        self.__page_items = int(self.__response.headers['page-items'])
        self.__data = self.__response.json()

        if "last" in self.__response.links:
            # We're on the last page
            self.__last = True

    def get_next(self):
        if not self.__last:
            self.__url = self.__response.links["next"]["url"]
            self.get_url()

    def get_data(self):
        return self.__response.json()

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

def get_registries():
    registry_url = "https://packages.ecosyste.ms/api/v1/registries"
    session = EcosystemsSession(registry_url)

    registries = []

    for i in session:
        registries.append(Registry(i))

    return registries


def get_packages(registry="pypi.org"):

    registry_url = f"https://packages.ecosyste.ms/api/v1/registries/{registry}/packages?per_page=100"
    session = EcosystemsSession(registry_url)

    for i in session:
        print(i)

