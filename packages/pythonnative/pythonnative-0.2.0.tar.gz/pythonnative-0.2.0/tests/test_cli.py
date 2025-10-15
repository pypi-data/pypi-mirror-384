import os
import shutil
import subprocess
import sys
import tempfile


def run_pn(args, cwd):
    cmd = [sys.executable, "-m", "pythonnative.cli.pn"] + args
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def test_cli_init_and_clean():
    tmpdir = tempfile.mkdtemp(prefix="pn_cli_test_")
    try:
        # init
        result = run_pn(["init", "MyApp"], tmpdir)
        assert result.returncode == 0, result.stderr
        assert os.path.isdir(os.path.join(tmpdir, "app"))
        # scaffolded entrypoint
        main_page_path = os.path.join(tmpdir, "app", "main_page.py")
        assert os.path.isfile(main_page_path)
        with open(main_page_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "def bootstrap(" in content
        assert os.path.isfile(os.path.join(tmpdir, "pythonnative.json"))
        assert os.path.isfile(os.path.join(tmpdir, "requirements.txt"))
        assert os.path.isfile(os.path.join(tmpdir, ".gitignore"))

        # clean (on empty build should be no-op)
        result = run_pn(["clean"], tmpdir)
        assert result.returncode == 0, result.stderr

        # create build dir and ensure clean removes it
        os.makedirs(os.path.join(tmpdir, "build", "android"), exist_ok=True)
        result = run_pn(["clean"], tmpdir)
        assert result.returncode == 0, result.stderr
        assert not os.path.exists(os.path.join(tmpdir, "build"))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_cli_run_prepare_only_android_and_ios():
    tmpdir = tempfile.mkdtemp(prefix="pn_cli_test_")
    try:
        # init to create app scaffold
        result = run_pn(["init", "MyApp"], tmpdir)
        assert result.returncode == 0, result.stderr

        # prepare-only android
        result = run_pn(["run", "android", "--prepare-only"], tmpdir)
        assert result.returncode == 0, result.stderr
        assert os.path.isdir(os.path.join(tmpdir, "build", "android", "android_template"))

        # prepare-only ios
        result = run_pn(["run", "ios", "--prepare-only"], tmpdir)
        assert result.returncode == 0, result.stderr
        assert os.path.isdir(os.path.join(tmpdir, "build", "ios", "ios_template"))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
