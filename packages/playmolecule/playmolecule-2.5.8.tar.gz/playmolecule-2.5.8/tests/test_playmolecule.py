from glob import glob
import json
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))


def prepare(datadir):
    outdir = str(datadir.join("out"))
    scratchdir = str(datadir.join("scratch"))
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(scratchdir, exist_ok=True)
    return outdir, scratchdir


def _test_old_playmolecule_manifests():
    os.environ["PM_APP_ROOT"] = os.path.join(curr_dir, "test_playmolecule")

    from playmolecule import apps, datasets, protocols
    import tempfile

    assert hasattr(apps, "proteinprepare")
    assert hasattr(apps.proteinprepare, "files")
    assert hasattr(apps.proteinprepare, "proteinprepare")
    assert hasattr(apps.proteinprepare.v1, "proteinprepare")
    assert hasattr(apps.proteinprepare.v1, "files")
    assert hasattr(apps.proteinprepare.v1.proteinprepare, "tests")
    assert hasattr(apps.proteinprepare.v1.proteinprepare.tests, "simple")
    assert sorted(list(apps.proteinprepare.v1.files.keys())) == sorted(
        [
            "datasets",
            "datasets/3ptb.pdb",
            "tests",
            "tests/web_content.pickle",
            "tests/reprepare.pickle",
            "tests/3ptb.pdb",
            "tests/587HG92V.pdb",
            "tutorials",
            "tutorials/learn_this_app.ipynb",
        ]
    )
    assert hasattr(apps.proteinprepare.v1.datasets, "file_3ptb")
    assert hasattr(datasets, "file_3ptb")
    assert hasattr(protocols, "crypticscout")
    assert hasattr(protocols.crypticscout, "v1")
    assert hasattr(protocols.crypticscout.v1, "crypticscout")
    assert hasattr(protocols.crypticscout.v1.crypticscout, "crypticscout")
    assert callable(protocols.crypticscout.v1.crypticscout.crypticscout)

    expected_files = [
        "run_*.sh",
        "run_*/",
        "run_*/expected_outputs.json",
        "run_*/.pm.done",
        "run_*/.manifest.json",
        os.path.join("run_*", "inputs.json"),
        os.path.join("run_*", "original_paths.json"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        apps.proteinprepare.proteinprepare(tmpdir, pdbfile=datasets.file_3ptb).run()
        for ef in expected_files:
            assert len(glob(os.path.join(tmpdir, ef))), "could not find " + ef

        with open(glob(os.path.join(tmpdir, "run_*", "inputs.json"))[0], "r") as f:
            inputs = json.load(f)
            assert "function" not in inputs

    expected_files += [os.path.join("run_*", "3ptb.pdb")]
    with tempfile.TemporaryDirectory() as tmpdir:
        apps.proteinprepare.proteinprepare(
            tmpdir,
            pdbfile=os.path.join(curr_dir, "test_playmolecule", "datasets", "3ptb.pdb"),
        ).run()
        for ef in expected_files:
            assert len(glob(os.path.join(tmpdir, ef))), "could not find " + ef


def _test_new_playmolecule_manifests():
    os.environ["PM_APP_ROOT"] = os.path.join(curr_dir, "test_playmolecule")

    from playmolecule import apps, datasets
    import tempfile

    assert hasattr(apps, "proteinpreparenew")
    assert hasattr(apps.proteinpreparenew, "proteinpreparenew")
    assert hasattr(apps.proteinpreparenew, "files")
    assert hasattr(apps.proteinpreparenew.v1, "proteinpreparenew")
    assert hasattr(apps.proteinpreparenew.v1, "files")
    assert hasattr(apps.proteinpreparenew.v1.proteinpreparenew, "tests")
    assert hasattr(apps.proteinpreparenew.v1.proteinpreparenew.tests, "simple")
    assert hasattr(apps.proteinpreparenew.v2, "proteinpreparenew")
    assert hasattr(apps.proteinpreparenew.v2, "files")
    assert hasattr(apps.proteinpreparenew.v2.proteinpreparenew, "tests")
    assert hasattr(apps.proteinpreparenew.v2.proteinpreparenew.tests, "simple")
    assert sorted(list(apps.proteinpreparenew.v1.files.keys())) == sorted(
        [
            "datasets",
            "datasets/3ptb.pdb",
            "tests",
            "tests/web_content.pickle",
            "tests/reprepare.pickle",
            "tests/3ptb.pdb",
            "tests/587HG92V.pdb",
            "tutorials",
            "tutorials/learn_this_app.ipynb",
        ]
    )
    assert hasattr(apps.proteinpreparenew.v1.datasets, "file_3ptb")
    assert hasattr(datasets, "file_3ptb")

    expected_files = [
        "run_*.sh",
        "run_*/",
        "run_*/.pm.done",
        "run_*/.manifest.json",
        "run_*/expected_outputs.json",
        os.path.join("run_*", "inputs.json"),
        os.path.join("run_*", "original_paths.json"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        apps.proteinpreparenew.proteinpreparenew(
            tmpdir, pdbfile=datasets.file_3ptb
        ).run()
        for ef in expected_files:
            assert len(glob(os.path.join(tmpdir, ef))), "could not find " + ef

        with open(glob(os.path.join(tmpdir, "run_*", "inputs.json"))[0], "r") as f:
            inputs = json.load(f)
            assert "function" in inputs
            assert (
                inputs["function"] == "proteinprepare.apps.proteinpreparenew.app.main"
            )

    with tempfile.TemporaryDirectory() as tmpdir:
        apps.proteinpreparenew.v1.bar(tmpdir, pdbid="3ptb").run()
        for ef in expected_files:
            assert len(glob(os.path.join(tmpdir, ef))), "could not find " + ef

        with open(glob(os.path.join(tmpdir, "run_*", "inputs.json"))[0], "r") as f:
            inputs = json.load(f)
            assert "function" in inputs
            assert inputs["function"] == "proteinprepare.apps.proteinpreparenew.app.bar"

    expected_files += [os.path.join("run_*", "3ptb.pdb")]
    with tempfile.TemporaryDirectory() as tmpdir:
        apps.proteinpreparenew.proteinpreparenew(
            tmpdir,
            pdbfile=os.path.join(curr_dir, "test_playmolecule", "datasets", "3ptb.pdb"),
        ).run()
        for ef in expected_files:
            assert len(glob(os.path.join(tmpdir, ef))), "could not find " + ef
