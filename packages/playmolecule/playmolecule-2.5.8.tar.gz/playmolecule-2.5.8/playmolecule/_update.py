# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import os
import zipfile
import tempfile
from glob import glob
import logging
import hashlib
import shutil

logger = logging.getLogger(__name__)
SHAREDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "share")

gcloud = None


def create_gcloud(credentials_file, license_checker=None):
    global gcloud
    gcloud = GCloudStorage(credentials_file, license_checker)


def download_data_location(force=False, default_cred_file=None, license_checker=None):
    import questionary

    if default_cred_file is not None and os.path.exists(default_cred_file):
        create_gcloud(default_cred_file, license_checker)
        return "gcloud"

    image_location_choices = [
        "Google Cloud (Requires internet connection)",
        "Local Directory (For offline installation. Requires large zip file provided by Acellera)",
    ]
    default = image_location_choices[0]

    try:
        image_location = questionary.select(
            "Where do you want to obtain the PlayMolecule images from? :",
            choices=image_location_choices,
            default=default,
            use_shortcuts=True,
        ).unsafe_ask()

        if image_location == image_location_choices[0]:
            # Get google cloud credentials
            gcloud_credentials = questionary.path(
                message="Path to google cloud credentials .json file:",
            ).unsafe_ask()
            shutil.copy(gcloud_credentials, default_cred_file)
            create_gcloud(default_cred_file, license_checker)
            image_location = "gcloud"
        elif image_location == image_location_choices[1]:
            # Get singularity image folder path
            image_location = questionary.path(
                message="Top folder containing the apptainer/singularity images:",
                only_directories=True,
            ).unsafe_ask()
            image_location = "local://" + os.path.abspath(image_location)
    except KeyboardInterrupt:
        raise RuntimeError("Setup interrupted by user. Please start again...")
    return image_location


def update_hashes(target):
    if os.path.isdir(target):
        target = glob(os.path.join(target, "*"))
    else:
        target = [target]

    for tgt in target:
        print(f"Generating MD5 hash for {target}")
        md5sum = hashlib.md5(open(tgt, "rb").read()).hexdigest()
        basename = os.path.basename(tgt)
        dirname = os.path.dirname(tgt)
        with open(os.path.join(dirname, f".{basename}.md5sum"), "w") as f:
            f.write(md5sum)


class GCloudStorage:
    def __init__(self, credentials_file, license_checker=None):
        from google.cloud import storage
        from google.oauth2 import service_account

        logger.info("Validating Google Cloud credentials")
        image_bucket_name = "228f801c-064c-46dd-b574-f9f56c1e8d1e"
        cred = service_account.Credentials.from_service_account_file(credentials_file)

        self.storage_client = storage.Client(project=cred._project_id, credentials=cred)
        self.image_bucket = self.storage_client.bucket(image_bucket_name)
        self.license_checker = license_checker
        self.licensed_apps = {}

    def download(self, source, target, _logger=True):
        if _logger:
            print(f"Downloading {source} from google cloud...")
        blob = self.image_bucket.blob(source)
        if not blob.exists():
            # print(f"{source} does not exist.")
            return
        blob.download_to_filename(target)

    def list_files(self, source):
        import subprocess
        from playmolecule import PM_APP_ROOT
        import re

        blobs = self.image_bucket.list_blobs(prefix=source, delimiter="/")
        # Order is important here. The prefixes variable is not populated until we iterate over blobs
        files = [blob.name for blob in blobs if not blob.name.endswith("/")]
        files += list(blobs.prefixes)

        with open(os.path.join(PM_APP_ROOT, "license_path.txt"), "r") as f:
            licence_path = f.read().strip()
        env = os.environ.copy()
        env["ACELLERA_LICENSE_SERVER"] = licence_path

        if self.license_checker:
            # Only show licensed apps to not confuse the user
            licensed_files = []
            for ff in files:
                match = re.search(r"pmws-apps/(\w+)_(v\d+)/", ff)
                if match is None:
                    continue
                app_name = match[1]
                app_version = match[2]
                if app_name in self.licensed_apps:
                    if not self.licensed_apps[app_name]:
                        continue
                else:
                    retcode = subprocess.call(
                        [
                            self.license_checker,
                            "-name",
                            app_name,
                            "-version",
                            app_version[1:],
                        ],
                        stdout=subprocess.DEVNULL,
                        env=env,
                    )
                    self.licensed_apps[app_name] = retcode == 0

                if self.licensed_apps[app_name]:
                    licensed_files.append(ff)
            files = licensed_files
        return sorted(files)


class LocalStorage:
    def __init__(self, data_location, license_checker=None):
        self.data_location = data_location.replace("local://", "")
        self.license_checker = license_checker

    def download(self, source, target, _logger=True):
        if not os.path.exists(os.path.join(self.data_location, source)):
            return
        shutil.copy(os.path.join(self.data_location, source), target)

    def list_files(self, source):
        from glob import glob

        files = []
        for ff in glob(os.path.join(self.data_location, source, "*")):
            if os.path.isdir(ff) and not ff.endswith("/"):
                ff = os.path.relpath(ff, os.path.abspath(self.data_location))
                ff = ff + "/"
            else:
                ff = os.path.relpath(ff, os.path.abspath(self.data_location))
            if self.license_checker:
                raise NotImplementedError(
                    "Add license checking"
                )  # TODO: Check if license exists
            files.append(ff)

        return files


class DataDownloader:
    def __init__(self, data_location, license_checker=None):
        if data_location.startswith("local:///"):
            self.storage = LocalStorage(data_location, license_checker)
        else:
            self.storage = gcloud

    def download(self, source, target, _logger=True):
        if source.endswith("/"):
            directory_mode = True
            files = self.storage.list_files(source)
        else:
            directory_mode = False
            files = [source]

        for ff in files:
            dest = target
            if directory_mode or os.path.isdir(target):
                dest = os.path.join(target, os.path.basename(ff))

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            self.storage.download(ff, dest, _logger=_logger)

    def list_files(self, source):
        return self.storage.list_files(source)


def compare_hashes(source, local_hash_loc, remote_hash_loc):
    from tqdm import tqdm

    download = True
    source_dir = os.path.dirname(remote_hash_loc)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Compare hashes
        tgt = os.path.join(tmpdir, "md5sum")
        source.download(remote_hash_loc, tgt, _logger=False)
        if not os.path.exists(tgt):
            return False

        with open(tgt, "r") as f:
            remote_hash = f.read().strip()

        try:
            if not os.path.exists(local_hash_loc):
                tqdm.write(f"No hashes found locally for {source_dir}. Downloading.")
                return True

            # Download local hash and read
            with open(local_hash_loc, "r") as f:
                local_hash = f.read().strip()

            if local_hash == remote_hash:
                download = False
                tqdm.write(f"Hashes for {source_dir} matched. Skipping download.")
            else:
                tqdm.write(f"Hashes for {source_dir} were different. Downloading.")

        except Exception as e:
            print(f"Failed to get current app hash with error {e}")
            # If there was some crash re-download anyway
            download = True
            pass
    return download


def _update_app_image(datadl, app, appname, outdir):
    hashname = f".{appname}.md5sum"
    manifestname = f"{appname}.json"

    # Compare hashes
    download = compare_hashes(
        datadl, os.path.join(outdir, hashname), f"{app}{hashname}"
    )
    if not download:
        return

    datadl.download(f"{app}{appname}", outdir)
    datadl.download(f"{app}{hashname}", outdir, _logger=False)
    datadl.download(f"{app}{manifestname}", outdir, _logger=False)


def _update_app_examples(datadl, app, outdir):
    examplename = "examples.zip"
    hashname = "examples.md5sum"

    # Compare hashes
    download = compare_hashes(
        datadl, os.path.join(outdir, hashname), f"{app}examples/{hashname}"
    )
    if not download:
        return

    datadl.download(f"{app}examples/{examplename}", outdir)
    datadl.download(f"{app}examples/{hashname}", outdir, _logger=False)

    zipname = os.path.join(outdir, examplename)
    if os.path.exists(zipname):
        with zipfile.ZipFile(zipname, "r") as zip_ref:
            zip_ref.extractall(outdir)
        os.remove(zipname)


def _update_app_tests(datadl, app, outdir):
    testname = "tests.zip"
    hashname = "tests.md5sum"

    outdir = os.path.join(outdir, "files")
    os.makedirs(outdir, exist_ok=True)

    # Compare hashes
    download = compare_hashes(
        datadl, os.path.join(outdir, hashname), f"{app}tests/{hashname}"
    )
    if not download:
        return

    datadl.download(f"{app}tests/{testname}", outdir)
    datadl.download(f"{app}tests/{hashname}", outdir, _logger=False)

    zipname = os.path.join(outdir, testname)
    if os.path.exists(zipname):
        with zipfile.ZipFile(zipname, "r") as zip_ref:
            zip_ref.extractall(outdir)
        os.remove(zipname)


def _update_app_datasets(datadl, app, appname, outdir):
    datasetname = "datasets.zip"
    hashname = "datasets.md5sum"

    outdir = os.path.join(outdir, "files")
    os.makedirs(outdir, exist_ok=True)

    # Compare hashes
    download = compare_hashes(
        datadl, os.path.join(outdir, hashname), f"{app}datasets/{hashname}"
    )
    if not download:
        return

    datadl.download(f"{app}datasets/{datasetname}", outdir)
    datadl.download(f"{app}datasets/{hashname}", outdir, _logger=False)
    print(f"Updating datasets for {appname}")

    zipname = os.path.join(outdir, datasetname)
    if os.path.exists(zipname):
        with zipfile.ZipFile(zipname, "r") as zip_ref:
            zip_ref.extractall(outdir)
        os.remove(zipname)


def _update_app_artifacts(datadl, app, appname, outdir):
    datasetname = "artifacts.zip"
    hashname = "artifacts.md5sum"

    os.makedirs(outdir, exist_ok=True)

    # Compare hashes
    download = compare_hashes(
        datadl, os.path.join(outdir, hashname), f"{app}artifacts/{hashname}"
    )
    if not download:
        return

    datadl.download(f"{app}artifacts/{datasetname}", outdir)
    datadl.download(f"{app}artifacts/{hashname}", outdir, _logger=False)
    print(f"Updating artifacts for {appname}")

    zipname = os.path.join(outdir, datasetname)
    if os.path.exists(zipname):
        with zipfile.ZipFile(zipname, "r") as zip_ref:
            zip_ref.extractall(outdir)
        os.remove(zipname)


def _update_protocols(datadl, app, outdir):
    datasetname = "acellera-protocols.zip"
    hashname = "acellera-protocols.zip.md5sum"

    outdir = os.path.join(outdir, "acellera-protocols")
    os.makedirs(outdir, exist_ok=True)

    # Compare hashes
    download = compare_hashes(
        datadl, os.path.join(outdir, hashname), f"{app}{hashname}"
    )
    if not download:
        return

    datadl.download(f"{app}{datasetname}", outdir)
    datadl.download(f"{app}{hashname}", outdir, _logger=False)
    print("Updating acellera-protocols")

    zipname = os.path.join(outdir, datasetname)
    if os.path.exists(zipname):
        with zipfile.ZipFile(zipname, "r") as zip_ref:
            zip_ref.extractall(outdir)
        os.remove(zipname)


def update_apps(mode="all", automatic=False):
    from playmolecule import PM_APP_ROOT
    from tqdm import tqdm
    import questionary
    import stat

    if PM_APP_ROOT is None:
        raise RuntimeError(f"Could not find PM_APP_ROOT environment variable")

    appdir = os.path.join(PM_APP_ROOT, "apps")

    service_acc_json = os.path.join(PM_APP_ROOT, "slpm-service-account.json")
    license_checker = os.path.join(SHAREDIR, "pm-licenses")
    data_location = download_data_location(
        default_cred_file=service_acc_json, license_checker=license_checker
    )

    datadl = DataDownloader(data_location, license_checker)
    apps = datadl.list_files("pmws-apps/")
    apps += ["acellera-protocols/"]

    if len(apps) == 0:
        print(
            "Could not find any apps. You have probably not set up the license server correctly. Set the ACELLERA_LICENSE_SERVER to the port@ip of the license server."
        )
        return

    choices = ["Download all apps", *apps]
    if not automatic:
        try:
            answer = questionary.select(
                "Which app do you want to download?", choices=choices
            ).unsafe_ask()
        except KeyboardInterrupt:
            return
    else:
        answer = "Download all apps"

    if choices.index(answer) == 0:
        answer = apps
    else:
        answer = [answer]

    for app in tqdm(answer, desc="Checking hashes and updating"):
        appname = os.path.basename(os.path.abspath(app))
        name = "_".join(appname.split("_")[:-1])
        version = appname.split("_")[-1]
        outdir = os.path.join(appdir, name.lower(), version)
        os.makedirs(outdir, exist_ok=True)

        artifacts = datadl.list_files(f"{app}artifacts/artifacts.zip")

        with open(os.path.join(outdir, "run.sh"), "w") as f:
            f.write(
                f'#!/bin/bash\nfilename=${{0%.sh}}\njob_dir=`dirname "$(realpath $0)"`\n{PM_APP_ROOT}/apptainer_run.sh {name.lower()}/{version}/{appname} $job_dir $filename'
            )

        if app == "acellera-protocols/":
            _update_protocols(datadl, app, PM_APP_ROOT)
        if mode in ("all", "image"):
            _update_app_image(datadl, app, appname, outdir)
        if len(artifacts) and mode in ("all", "artifacts"):
            _update_app_artifacts(datadl, app, appname, outdir)
        if (
            len(artifacts) == 0
        ):  # TODO: Deprecate this once all apps server artifacts zip
            if mode in ("all", "examples"):
                _update_app_examples(datadl, app, outdir)
            if mode in ("all", "tests"):
                _update_app_tests(datadl, app, outdir)
            if mode in ("all", "datasets"):
                _update_app_datasets(datadl, app, appname, outdir)

    if mode in ("all", "image"):
        _update_app_image(datadl, "pmws-decrypter/", "pm-decrypter", appdir)
        pmdec = os.path.join(appdir, "pm-decrypter")
        st = os.stat(pmdec)
        os.chmod(pmdec, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
