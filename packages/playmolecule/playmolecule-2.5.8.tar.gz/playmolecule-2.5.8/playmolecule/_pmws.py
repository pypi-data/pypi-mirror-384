# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#


def _get_apps(server_endpoint, token):
    import json
    import requests

    print("Querying", f"{server_endpoint}/apps")
    rsp = requests.get(f"{server_endpoint}/apps", headers={"token": token})
    rsp.close()

    res = json.loads(rsp.text)
    apps = {}
    for app in res:
        name = app["name"].lower()

        if name not in apps:
            apps[name] = {}

        version = "v" + str(int(app["version"]))
        if version not in apps[name]:
            rsp = requests.get(
                f"{server_endpoint}/apps/{app['id']}/manifest", headers={"token": token}
            )
            rsp.close()
            manifest = json.loads(rsp.text)
            apps[name][version] = {"manifest": manifest, "appdir": None, "run.sh": None}

    return apps


def _set_root_pmws(sever_endpoint):
    from natsort import natsorted
    from playmolecule.apps import _manifest_to_func
    import os

    token = os.environ["PMWS_TOKEN"]

    app_manifests = _get_apps(sever_endpoint, token)

    for appname in app_manifests:
        latest = natsorted(app_manifests[appname].keys())[-1]
        _manifest_to_func(appname, app_manifests[appname], latest)
