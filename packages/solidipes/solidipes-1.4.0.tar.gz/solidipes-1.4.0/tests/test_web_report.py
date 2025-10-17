import os
import shutil
import signal
import subprocess
import time

import pytest
import utils

from solidipes.plugins.discovery import uploader_list

streamlit_port = 8504
max_connection_tries = 20
delay_connection_trial = 1
max_loading_checks = 20
delay_page_load = 1
test_download_dir = os.path.join(os.getcwd(), "_downloads")


@pytest.fixture()
def sb(request):
    from selenium import webdriver
    from seleniumbase import BaseCase

    class BaseClass(BaseCase):
        def get_new_driver(self, *args, **kwargs):
            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            self.download_dir = test_download_dir
            os.makedirs(self.download_dir, exist_ok=True)
            firefox_profile = {
                "browser.download.folderList": 2,
                "browser.download.dir": self.download_dir,
                "browser.helperApps.neverAsk.saveToDisk": "image/png",
                "pdfjs.disabled": True,
            }
            for key, value in firefox_profile.items():
                options.set_preference(key, value)
            return webdriver.Firefox(options=options)

        def setUp(self) -> None:
            super().setUp()

        def base_method(self) -> None:
            pass

        def tearDown(self) -> None:
            self.save_teardown_screenshot()
            super().tearDown()

    sb = BaseClass("base_method")
    sb.setUpClass()
    sb.setUp()
    yield sb
    sb.tearDown()
    sb.tearDownClass()


class WebReportLauncher:
    def __init__(self) -> None:
        self.streamlit_subprocess = None
        self.out = None
        self.err = None

    def launch(self, dir_path):
        self.streamlit_subprocess = subprocess.Popen(
            [
                "solidipes",
                "report",
                "web-report",
                ".",
                "--server.port",
                str(streamlit_port),
                "--server.headless",
                "true",
            ],
            cwd=dir_path,
            preexec_fn=os.setsid,
        )
        if self.streamlit_subprocess.returncode is not None and self.streamlit_subprocess.returncode != 0:
            raise RuntimeError("Could not start web report")
        return self

    def check_running(self, delay):
        if not self.streamlit_subprocess:
            return False

        try:
            self.streamlit_subprocess.wait(timeout=delay)
            self.out, self.err = self.streamlit_subprocess.communicate(timeout=0)
            self.streamlit_subprocess = None
            return False
        except subprocess.TimeoutExpired:
            return True

    def terminate(self):
        if not self.streamlit_subprocess:
            return
        try:
            os.killpg(os.getpgid(self.streamlit_subprocess.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        self.check_running(5)

    def get_outputs(self):
        return self.out, self.err


@pytest.fixture()
def web_report():
    web_report_launcher = WebReportLauncher()
    yield web_report_launcher
    web_report_launcher.terminate()


def init_study_dir(tmp_path, solidipes=True, git=False, git_remote=False):
    dir_path = tmp_path / "study"
    if not os.path.exists(f"{tmp_path}/study"):
        dir_path.mkdir()
    if solidipes:
        subprocess.run(["solidipes", "init"], cwd=dir_path)
    if git or git_remote:
        subprocess.run(["git", "init", "-q"], cwd=dir_path)
    if git_remote:
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://domain.com/subdomain/user_name/project_name.git",
            ],
            cwd=dir_path,
        )
    return dir_path


def check_streamlit_is_loading(sb):
    return sb.is_element_present('div[data-testid="stStatusWidget"]')


def start_web_report_without_fault(sb, dir_path, web_report, target="?page=curation") -> None:
    web_report.launch(dir_path)
    url = f"http://localhost:{streamlit_port}/{target}"
    for i in range(max_connection_tries):
        if not web_report.check_running(delay_connection_trial):
            raise RuntimeError("Web report is not running")
        try:
            sb.open(url)
            break
        except Exception:
            pass
    if i == max_connection_tries - 1:
        raise RuntimeError("Could not connect to Streamlit web report")

    for i in range(max_loading_checks):
        if not web_report.check_running(delay_page_load):
            raise RuntimeError("Web report is not running")
        if not check_streamlit_is_loading(sb):
            break
    if i == max_loading_checks - 1:
        raise RuntimeError("Streamlit web report stuck in loading state")

    time.sleep(delay_page_load)


def gracefully_stop_report(web_report) -> None:
    web_report.terminate()
    _, streamlit_errors = web_report.get_outputs()
    streamlit_errors = str(streamlit_errors).replace("\\n", "\n")
    error_found = "Traceback" in streamlit_errors or "already in use" in streamlit_errors
    if error_found:
        raise RuntimeError("Error encountered in Streamlit: \n{}".format(streamlit_errors))


def check_streamlit_errors(sb, dir_path, web_report, target="?page=curation") -> None:
    start_web_report_without_fault(sb, dir_path, web_report, target)
    gracefully_stop_report(web_report)


def test_web_report(sb, tmp_path, web_report) -> None:
    dir_path = init_study_dir(tmp_path)
    check_streamlit_errors(sb, dir_path, web_report)


def test_web_report_without_solidipes(sb, tmp_path, web_report) -> None:
    dir_path = init_study_dir(tmp_path, solidipes=False)
    with pytest.raises(RuntimeError):
        check_streamlit_errors(sb, dir_path, web_report)


def test_web_report_with_git(sb, tmp_path, web_report) -> None:
    dir_path = init_study_dir(tmp_path, git=True)
    check_streamlit_errors(sb, dir_path, web_report)


def test_web_report_with_git_remote(sb, tmp_path, web_report) -> None:
    dir_path = init_study_dir(tmp_path, git_remote=True)
    check_streamlit_errors(sb, dir_path, web_report)


@pytest.mark.parametrize("step_name", ["acquisition", "curation", "metadata", "export"])
def test_pages_loading(sb, tmp_path, web_report, step_name: str) -> None:
    """Test that each page loads without errors."""

    dir_path = init_study_dir(tmp_path)
    check_streamlit_errors(sb, dir_path, web_report, target=f"?page={step_name}")


@pytest.mark.parametrize("uploader_name", [u.parser_key for u in uploader_list])
def test_export_pages_loading(sb, tmp_path, web_report, uploader_name: str) -> None:
    """Test that each export sub-page loads without errors."""

    dir_path = init_study_dir(tmp_path)
    check_streamlit_errors(sb, dir_path, web_report, target=f"?page=export&uploader={uploader_name}")


def test_display_file(sb, tmp_path, web_report) -> None:
    dir_path = init_study_dir(tmp_path)

    # Add text file
    data_path = os.path.join(dir_path, "data")
    os.makedirs(data_path, exist_ok=True)
    shutil.copy(utils.get_asset_path("text.txt"), data_path)

    # Check web report
    check_streamlit_errors(sb, dir_path, web_report, target="?page=display_page&file=./data/text.txt")


# @pytest.mark.skip(reason="needs to manipulate cache to fix it")
def test_display_file_sequence(sb, tmp_path, web_report) -> None:
    dir_path = init_study_dir(tmp_path)

    # Add sequence of files
    data_path = os.path.join(dir_path, "data")
    element_paths = [os.path.join(data_path, f"element_{i}.txt") for i in range(3)]
    os.makedirs(data_path, exist_ok=True)
    for element_path in element_paths:
        shutil.copy(utils.get_asset_path("text.txt"), element_path)

    # Check web report
    check_streamlit_errors(
        sb,
        dir_path,
        web_report,
        target=f"?page=display_page&file=element_*.txt&paths={','.join(element_paths)}&loader=FileSequence",
    )
