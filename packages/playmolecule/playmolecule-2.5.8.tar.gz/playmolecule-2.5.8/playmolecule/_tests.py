# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import re


class _Tests:
    def __init__(self, config, func, files, artifacts) -> None:
        if files is None:
            return

        for key in config:
            attr_name = key

            # Ensure attribute name starts with a letter
            if not attr_name[0].isalpha():
                attr_name = f"test_{attr_name}"

            # Replace non-alphanumeric (and _) characters with _
            attr_name = re.sub(r"[^a-zA-Z0-9_]", "_", attr_name)

            try:
                setattr(
                    self,
                    attr_name,
                    _Test(attr_name, config[key], func, files, artifacts),
                )
            except Exception:
                import traceback

                print(
                    f"Failed to set-up test {key} for function {func.__name__} with traceback: {traceback.format_exc()}"
                )

    def __str__(self) -> str:
        descr = ""
        for key in self.__dict__:
            descr += f"{self.__dict__[key]}\n"
        return descr

    def __repr__(self) -> str:
        return self.__str__()


def _convert_test_files(func_name, test_name, file_name, files, artifacts):
    if file_name.startswith("tests/"):
        if file_name.endswith("/"):
            file_name = file_name[:-1]
        return files[file_name]
    if file_name.startswith("datasets/") or file_name.startswith("artifacts/"):
        file_name = file_name.replace("datasets/", "").replace("artifacts/", "")
        if artifacts is None:
            raise RuntimeError(
                f"Test {test_name} of function '{func_name}' requires file {file_name} but the app manifest is missing the artifacts section"
            )
        return getattr(artifacts, file_name)
    return file_name


class _Test:
    def __init__(self, test_name, config, func, files, artifacts) -> None:
        func_name = func.__name__
        args = config["arguments"].copy()
        for key, vals in args.items():
            if not isinstance(vals, (list, tuple)):
                vals = [vals]

            for i in range(len(vals)):
                val = vals[i]
                if isinstance(val, dict):
                    for k, file_name in val.items():
                        if not isinstance(file_name, str):
                            continue
                        val[k] = _convert_test_files(
                            func_name, test_name, file_name, files, artifacts
                        )
                if not isinstance(val, str):
                    continue
                vals[i] = _convert_test_files(
                    func_name, test_name, val, files, artifacts
                )
            args[key] = vals if len(vals) > 1 else vals[0]
        config["arguments"] = args

        self.func = func
        self.name = test_name
        self.config = config

    def run(self, queue=None, dir=None, **kwargs):
        """Run the test

        Parameters
        ----------
        queue : str
            The name of the queue on which to run the test. By default it will be run locally.
            For options check the documentation of the ExecutableDirectory.run method.
        dir : str, Path
            Directory in which to execute the tests. By default they will be executed under
            the /tmp/ folder. However this is usually not accessible over SLURM, therefore
            if queue="slurm" is used, choose a network mounted path in which to execute the tests.
        kwargs : dict
            Additional arguments for the queue execution. For options check the documentation
            of the ExecutableDirectory.run method.
        """
        from playmolecule import PM_APP_ROOT, JobStatus
        from playmolecule._appfiles import _File
        from glob import glob
        import tempfile
        import time
        import inspect
        import os

        with tempfile.TemporaryDirectory(dir=dir) as tmpdir:
            testargs = self.config["arguments"].copy()
            func_sig = inspect.signature(self.func).parameters
            if "outdir" in func_sig:
                testargs["outdir"] = tmpdir
            if "execdir" in func_sig:
                tmpdir = testargs["execdir"]
                if isinstance(tmpdir, _File):
                    tmpdir = tmpdir.path

            print(
                f"Running test '{self.name}' at location {tmpdir} with args {testargs}"
            )

            t = time.time()

            ed = self.func(**testargs)
            ed.run(queue=queue, **kwargs)

            while ed.status not in (JobStatus.COMPLETED, JobStatus.ERROR):
                time.sleep(10)

            for ff in self.config["expected_outputs"]:
                if len(glob(os.path.join(tmpdir, ff))) == 0:
                    raise RuntimeError(
                        f"Test failed. Could not find expected output file: {ff} in {tmpdir}"
                    )
            print(
                f"\n🎉 Test '{self.name}' succeeded in {time.time()-t:.2f} seconds! 🎉"
            )

    def __str__(self) -> str:
        descr = self.config["description"]
        string = f"[{self.name}] '{descr}'\n- Arguments:\n"
        for arg, val in self.config["arguments"].items():
            string += f"  {arg} = {val}\n"
        string += "- Expected outputs:\n"
        for outp in self.config["expected_outputs"]:
            string += f"  {outp}\n"
        return string

    def __repr__(self) -> str:
        return self.__str__()
