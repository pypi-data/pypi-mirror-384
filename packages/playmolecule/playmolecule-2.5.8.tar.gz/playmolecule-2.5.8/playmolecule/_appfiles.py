# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
class _Artifacts:
    def __init__(self, artifacts, files_dict) -> None:
        from playmolecule import PM_APP_ROOT
        import os

        searchpaths = [
            ["datasets"],
            ["artifacts"],
            ["files", "datasets"],
            ["files", "artifacts"],
            [],
        ]

        for ds in artifacts:
            path = None
            for sp in searchpaths:
                if not PM_APP_ROOT.startswith("http"):
                    path = os.path.join(*sp, ds["path"])
                else:
                    path = ds["remotepath"]
                if path in files_dict:
                    break

            if path is None:
                raise RuntimeError(
                    f"Could not find dataset {ds['name']} at path {path}"
                )

            try:
                if "." in ds["name"]:
                    raise RuntimeError(
                        f"Dataset/artifact names cannot include dots in the name. {ds['name']} contains a dot."
                    )
                if not ds["name"][0].isalpha():
                    raise RuntimeError(
                        f"Dataset/artifact names must start with a letter. {ds['name']} does not."
                    )
                setattr(
                    self,
                    ds["name"],
                    _File(ds["name"], files_dict[path].path, ds["description"]),
                )
            except Exception:
                pass

    def __str__(self) -> str:
        descr = ""
        for key in self.__dict__:
            descr += f"{self.__dict__[key]}\n"
        return descr

    def __repr__(self) -> str:
        return self.__str__()


class _File:
    def __init__(self, name, path, description=None) -> None:
        self.name = name
        self.path = path
        self.description = description

    def __str__(self) -> str:
        string = f"[{self.name}] {self.path}"
        if self.description is not None:
            string += f" '{self.description}'"
        return string

    def __repr__(self) -> str:
        return self.__str__()


def _get_app_files(source_dir, appname=None, appversion=None):
    from playmolecule import PM_APP_ROOT
    from glob import glob
    import os

    if PM_APP_ROOT.startswith("http"):
        return _get_app_files_pmws(appname, appversion)

    files = {}

    for ff in glob(os.path.join(source_dir, "**", "*"), recursive=True):
        fname = os.path.relpath(ff, source_dir)
        abspath = os.path.abspath(ff)
        files[fname] = _File(fname, abspath)

    return files


def _get_app_files_pmws(appname, appversion):
    from playmolecule import PM_APP_ROOT
    import requests
    import json
    import os

    appname = appname.lower()
    endpoint = PM_APP_ROOT
    token = os.environ["PMWS_TOKEN"]

    # Get app datasets
    files = {}
    rsp = requests.get(
        f"{endpoint}/datacenter",
        headers={
            "Content-type": "application/json",
            "Accept": "text/plain",
            "token": token,
            "tags": f"dataset:acellera,app:{appname}",
            "startsWith": f"{appname}/",
        },
    )
    rsp.close()
    if rsp is None:
        return None

    datasets = json.loads(rsp.text)

    for ds in datasets:
        name = ds["filepath"]
        path = f"dc://{ds['id']}"
        files[name] = _File(name, path, description=ds["comments"])

    # Get app test files
    rsp = requests.get(
        f"{endpoint}/datacenter",
        headers={
            "Content-type": "application/json",
            "Accept": "text/plain",
            "token": token,
            "tags": "apps:tests:file",
            "filePath": f"apps/{appname}_{appversion}/tests/file",
            "filelist": "True",
        },
    )
    rsp.close()
    if rsp is None:
        return None

    datasets = json.loads(rsp.text)
    assert len(datasets) <= 1
    if len(datasets):
        ds = datasets[0]
        if ds["files"] is not None:
            for ff in ds["files"]:
                while ff.endswith("/"):
                    ff = ff[:-1]
                name = ff
                path = f"dc://{ds['id']}?files={ff}"
                files[name] = _File(name, path)

    return files
