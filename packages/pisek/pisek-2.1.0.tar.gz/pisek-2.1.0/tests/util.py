import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

from pisek.config import config_hierarchy
from pisek.__main__ import test_task_path
from pisek.utils.util import clean_task_dir
from pisek.utils.pipeline_tools import is_task_dir


class TestFixture(unittest.TestCase):
    def fixture_path(self):
        return None

    def setUp(self):
        os.environ["PISEK_DIRECTORY"] = "../pisek"
        os.environ["LOG_LEVEL"] = "debug"

        if not self.fixture_path():
            return

        self.task_dir_orig = os.path.abspath(
            os.path.join(os.path.dirname(__file__), self.fixture_path())
        )
        self.fixtures_dir = tempfile.mkdtemp(prefix="pisek-test_")
        self.task_dir = os.path.join(
            self.fixtures_dir, os.path.relpath(self.fixture_path(), "../fixtures")
        )

        # shutil.copytree() requires that the destination directory does not exist,
        os.rmdir(self.fixtures_dir)
        shutil.copytree(
            self.task_dir_orig,
            os.path.join(self.fixtures_dir, os.path.basename(self.task_dir_orig)),
        )
        shutil.copytree(
            os.path.join(self.task_dir_orig, "../pisek"),
            os.path.join(self.fixtures_dir, "pisek"),
        )

        if not is_task_dir(
            self.task_dir,
            os.environ["PISEK_DIRECTORY"],
            config_hierarchy.DEFAULT_CONFIG_FILENAME,
        ):
            exit(1)
        clean_task_dir(self.task_dir, os.environ["PISEK_DIRECTORY"])

        self.cwd_orig = os.getcwd()
        os.chdir(self.task_dir)

    def runTest(self):
        # Implement this!
        pass

    def tearDown(self):
        if not self.fixture_path():
            return

        os.chdir(self.cwd_orig)

        assert self.fixtures_dir.startswith("/tmp") or self.fixtures_dir.startswith(
            "/var"
        )
        shutil.rmtree(self.fixtures_dir)

    def log_files(self):
        """Log all files for checking whether new ones have been created."""
        self.original_files = os.listdir(self.task_dir)

    def created_files(self):
        """Additional files that are expected to be created."""
        return []

    def check_files(self):
        """
        Check whether there are no new unexpected files.
        Ignored:
            .pisek_cache data/* build/*
        """
        directories = ["build", "tests", ".pisek"]
        files = [".pisek_cache"] + self.created_files()

        all_paths = set(self.original_files + directories + files)

        for path in os.listdir(self.task_dir):
            self.assertIn(
                path,
                all_paths,
                f"Pisek generated new file {path}.",
            )


class TestFixtureVariant(TestFixture):
    def expecting_success(self):
        return True

    def catch_exceptions(self):
        return False

    def modify_task(self):
        """
        Code which modifies the task before running the tests should go here.
        For example, if we want to check that the presence of `sample.in` is
        correctly checked for, we would remove the file here.
        """
        pass

    def runTest(self):
        if not self.fixture_path():
            return

        self.modify_task()
        self.log_files()

        # We lower the time limit to make the self-tests run faster. The solutions
        # run instantly, with the exception of `solve_slow_4b`, which takes 10 seconds
        # and we want to consider it a time limit
        @mock.patch("sys.stdout", new_callable=io.StringIO)
        @mock.patch("sys.stderr", new_callable=io.StringIO)
        def run(*args):
            return test_task_path(
                self.task_dir,
                inputs=1,
                strict=False,
                full=False,
                time_limit=0.2,
                plain=False,
                pisek_dir=os.environ["PISEK_DIRECTORY"],
            )

        runner = unittest.TextTestRunner(failfast=True)

        self.assertEqual(run(), not self.expecting_success())

        self.check_end_state()
        self.check_files()

    def check_end_state(self):
        # Here we can verify whether some conditions hold when Pisek finishes,
        # making sure that the end state is reasonable
        pass


def overwrite_file(task_dir, old_file, new_file, new_file_name=None):
    os.remove(os.path.join(task_dir, old_file))
    shutil.copy(
        os.path.join(task_dir, new_file),
        os.path.join(task_dir, new_file_name or old_file),
    )


def modify_config(task_dir: str, modification_fn):
    """
    `modification_fn` accepts the config (in "raw" ConfigParser format) and may
    modify it. The modified version is then saved.

    For example, if we want to change the evaluation method ("out_check")
    from `diff` to `judge`, we would do that in `modification_fn` via:
        config["tests"]["out_check"] = "judge"
        config["tests"]["out_judge"] = "judge"  # To specify the judge program file
    """

    config = config_hierarchy.new_config_parser()
    config_path = os.path.join(task_dir, config_hierarchy.DEFAULT_CONFIG_FILENAME)
    read_files = config.read(config_path)
    if not read_files:
        raise FileNotFoundError(f"Missing configuration file {config_path}.")

    modification_fn(config)

    with open(config_path, "w") as f:
        config.write(f)
