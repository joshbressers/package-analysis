#!/usr/bin/env python

import sys
import os
import json
import vulnerabilities
from esbulkstream import Documents
from pathlib import Path
from tqdm import tqdm

import dep_relationships

def retstr(i):
    if type(i) is not str:
        print("\n\n***")
        print(type(i))
        print(i)
        print("***\n\n")
        raise Exception("not a string")
    else:
        return i


file_dir = sys.argv[1]

dep_rel = dep_relationships.get_deps(file_dir)

es = Documents('npm-packages', mapping='', delete=True)
es_one = Documents('npm-one-package', mapping='', delete=True)

path = Path(file_dir)

vulns = vulnerabilities.Vulnerabilities()

progress_bar = tqdm(total=2174520)
for filename in path.rglob('*'):
    progress_bar.update()

    if os.path.isdir(filename):
        continue

    one_id = str(filename).split('/', 1)[1]
    one_data = { "name": one_id }

    if one_id in dep_rel:
        one_data['deps'] = dep_rel[one_id]

    if one_id.startswith('@'):
        # This is a scoped package
        one_data["scoped"] = True
        (scope, name) = one_id.split('/')
        one_data["scope"] = scope
        one_data["scope_name"] = name

    if not os.path.exists("downloads/%s" % one_id):
        continue

    with open("downloads/%s" % one_id, mode="r") as fh:
        try:
            data = json.loads(fh.read())
        except:
            progress_bar.close()
            print("Failed to read downloads/%s" % one_id)
            sys.exit(1)
        if data["package"] != one_id:
            progress_bar.close()
            print("%s download data might be broken" % one_id)
            sys.exit(1)
        one_data["downloads"] = data["downloads"]

    with open(filename, mode="r") as fh:
        data = json.loads(fh.read())

        data["downloads"] = one_data["downloads"]

        if "description" in data and data["description"] == "security holding package":
            one_data["security_holding"] = True

        if "name" not in data:
            #print("No name %s" % filename)
            one_data["withdrawn"] = True
            es_one.add(one_data, one_id)
            continue
        if "time" not in data:
            #print("No time %s" % filename)
            one_data["no_time"] = True
            es_one.add(one_data, one_id)
            continue
        package_name = data["name"]

        if "versions" in data:
            one_data["versions"] = len(data["versions"])
        elif "unpublished" in data["time"]:
            one_data["unpublished"] = True
            one_data["versions"] = len(data["time"]["unpublished"]["versions"])
        else:
            one_data["versions"] = len(data["time"])
            # The created and modified fields should always exist, but this
            # data gets pretty weird
            if one_data["versions"] > 2:
                one_data["versions"] = one_data["versions"] - 2

        one_data["vulnerabilities"] = 0

        all_vulns = []

        # Use this to see if the license changed

        for ver in data["time"].keys():

            # XXX Do something with these later
            #if ver == "created":
            #    continue
            #elif ver == "modified":
            #    continue
            if ver == "unpublished":
                continue

            # Figure out the licenses
            current_licenses = []
            if "versions" in data and ver in data["versions"]:
                if ver != "modified" and ver != "created":
                    # We see two types of license fields. Some are called
                    # "licenses" some are called "license"
                    if "licenses" in data["versions"][ver]:
                        if type(data["versions"][ver]["licenses"]) is str:
                            current_licenses.append(retstr(data["versions"][ver]["licenses"]))
                        elif type(data["versions"][ver]["licenses"]) is int:
                            next
                        elif type(data["versions"][ver]["licenses"]) is bool:
                            next
                        elif type(data["versions"][ver]["licenses"]) is dict:
                            if len(data["versions"][ver]["licenses"]) == 0:
                                next
                            elif "type" in data["versions"][ver]["licenses"]:
                                current_licenses.append(retstr(data["versions"][ver]["licenses"]["type"]))
                            elif "license" in data["versions"][ver]["licenses"]:
                                current_licenses.append(retstr(data["versions"][ver]["licenses"]["license"]))
                            else:
                                progress_bar.close()
                                print("\n\n*** type missing")
                                print(data["versions"][ver]["licenses"])
                                print("***\n\n")
                                sys.exit(1)
                        elif type(data["versions"][ver]["licenses"]) is list:
                            for l in data["versions"][ver]["licenses"]:
                                if type(l) is str:
                                    current_licenses.append(retstr(l))
                                else:
                                    if "type" in l:
                                        if type(l["type"]) is dict:
                                            if "type" in l["type"]:
                                                current_licenses.append(retstr(l["type"]["type"]))
                                            elif "name" in l["type"]:
                                                current_licenses.append(retstr(l["type"]["name"]))
                                        else:
                                            current_licenses.append(retstr(l["type"]))
                                    elif "name" in l:
                                        if type(l["name"]) is dict:
                                            if "type" in l["name"]:
                                                current_licenses.append(retstr(l["name"]["type"]))
                                            elif "name" in l["name"]:
                                                current_licenses.append(retstr(l["name"]["name"]))
                                        else:
                                            current_licenses.append(retstr(l["name"]))
                                    elif "license" in l:
                                        current_licenses.append(retstr(l["license"]))
                                    elif "licence" in l:
                                        current_licenses.append(retstr(l["licence"]))
                                    elif "type" in l:
                                        current_licenses.append(retstr(l["type"]))
                                    elif "type:" in l:
                                        current_licenses.append(retstr(l["type:"]))
                                    elif " type" in l:
                                        current_licenses.append(retstr(l[" type"]))
                                    elif "MIT" in l:
                                        current_licenses.append(retstr("MIT"))
                                    elif "url" in l:
                                        next
                                    elif len(l) == 0:
                                        next
                                    else:
                                        print("\n\n***")
                                        print(l)
                                        print("***\n\n")
                                        raise Exception("Something weird happened")
                        else:
                            progress_bar.close()
                            print("\n\n*** licenses else")
                            print(data["versions"][ver]["licenses"])
                            print("\n\n***")
                            sys.exit(1)
                    elif "license" in data["versions"][ver]:
                        if type(data["versions"][ver]["license"]) is str:
                            current_licenses.append(retstr(data["versions"][ver]["license"]))
                        elif data["versions"][ver]["license"] is None:
                            next
                        elif type(data["versions"][ver]["license"]) is dict:
                            if len(data["versions"][ver]["license"]) == 0:
                                next
                            elif "notValid" in data["versions"][ver]["license"]:
                                next
                            elif "type" in data["versions"][ver]["license"]:
                                current_licenses.append(retstr(data["versions"][ver]["license"]["type"]))
                            elif "license" in data["versions"][ver]["license"]:
                                current_licenses.append(retstr(data["versions"][ver]["license"]["license"]))
                            elif "name" in data["versions"][ver]["license"]:
                                if type(data["versions"][ver]["license"]["name"]) is dict:
                                    next
                                else:
                                    current_licenses.append(retstr(data["versions"][ver]["license"]["name"]))
                            elif "key" in data["versions"][ver]["license"]:
                                current_licenses.append(retstr(data["versions"][ver]["license"]["key"]))
                            elif "prefered" in data["versions"][ver]["license"]:
                                current_licenses.append(retstr(data["versions"][ver]["license"]["prefered"]))
                            elif "sourceType" in data["versions"][ver]["license"]:
                                current_licenses.append(retstr(data["versions"][ver]["license"]["sourceType"]))
                            elif "cool" in data["versions"][ver]["license"]:
                                next
                            elif "rad" in data["versions"][ver]["license"]:
                                next
                            elif "url" in data["versions"][ver]["license"]:
                                next
                            else:
                                progress_bar.close()
                                print("\n\n*** dict type")
                                print(data["versions"][ver]["license"])
                                print("\n\n***")
                                sys.exit(1)
                        elif type(data["versions"][ver]["license"]) is list:
                            for l in data["versions"][ver]["license"]:
                                if type(l) is str:
                                    current_licenses.append(retstr(l))
                                elif type(l) is list:
                                    next
                                elif type(l) is dict:
                                    try:
                                        if "name" in l:
                                            current_licenses.append(retstr(l["name"]))
                                        elif "type" in l:
                                            current_licenses.append(retstr(l["type"]))
                                    except:
                                        progress_bar.close()
                                        print("\n\n*** l name")
                                        print(l)
                                        print("\n\n***")
                                        sys.exit(1)
                                else:
                                    try:
                                        current_licenses.append(retstr(l["type"]))
                                    except:
                                        progress_bar.close()
                                        print("\n\n*** l tpe")
                                        print(type(l))
                                        print(l)
                                        print("\n\n***")
                                        sys.exit(1)
                        elif type(data["versions"][ver]["license"]) is int:
                            next
                        elif type(data["versions"][ver]["license"]) is bool:
                            next
                        else:
                            progress_bar.close()
                            print("\n\n*** license")
                            print(data["versions"][ver]["license"])
                            print(type(data["versions"][ver]["license"]))
                            print("\n\n***")
                            sys.exit(1)

            package_version = ver
            package_time = data["time"][ver]

            doc_id = "%s-%s" % (package_name, package_version)

            doc = {
                "name": package_name,
                "version": package_version,
                "num_licenses": len(current_licenses),
                "licenses": current_licenses,
                "date": package_time,
                "vulnerabilities": vulns.match(package_name, package_version),
                "downloads" : data["downloads"]
            }

            one_data["vulnerabilities"] += len(doc["vulnerabilities"])
            all_vulns.extend(doc["vulnerabilities"])

            if package_name in dep_rel:
                doc['deps'] = dep_rel[package_name]

            es.add(doc, doc_id)


        one_data["unique_vulnerabilities"] = len(set(all_vulns))
        es_one.add(one_data, one_id)


es.done()
es_one.done()
