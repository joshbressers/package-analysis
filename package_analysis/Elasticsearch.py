
from esbulkstream import Documents
import logging


class PackageAnalysisES:

    def __init__(self):
        self.package_es = Documents('patest-ecosystems-packages', mapping='', delete=False)
        self.versions_es = Documents('patest-ecosystems-versions', mapping='', delete=False)

    def get_latest_package(self, registry):
        es_handle = self.package_es.es

        try:
            data = es_handle.search(index="patest-ecosystems-packages",
                aggs={"max_date": {"max": {"field": "updated_at"}}},
                body={"query": {"bool" : { "must" : { "term" : { "repo.keyword" : registry }}}}},
                size=0
            )
        except:
            return "1979-01-01"

        if "value_as_string" in data["aggregations"]["max_date"]:
            return data["aggregations"]["max_date"]["value_as_string"]
        else:
            return "1979-01-01"

    def add_package(self, package):
        doc_id = "%s-%s" % (package["repo"], package["name"])
        error = None
        try:
            error = self.package_es.add(package, doc_id)
        except Exception as e:
            logging.warn("Package Output: Something bad happened")
            logging.warn(e)
            logging.warn(error)

    def add_version(self, version):
        doc_id = "%s-%s-%s" % (version["repo"], version["name"], version["number"])
        error = None
        try:
            error = self.versions_es.add(version, doc_id)
        except Exception as e:
            logging.warn("Version Output: Something bad happened")
            logging.warn(e)
            logging.warn(error)

    def done(self):
        self.package_es.done()
        self.versions_es.done()
