import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import urllib.request
from importlib import resources
from typing import Any, Dict, List, Optional


def init_project(args: argparse.Namespace) -> None:
    """
    Initialize a new PythonNative project.
    Creates `app/`, `pythonnative.json`, `requirements.txt`, `.gitignore`.
    """
    project_name: str = getattr(args, "name", None) or os.path.basename(os.getcwd())
    cwd: str = os.getcwd()

    app_dir = os.path.join(cwd, "app")
    config_path = os.path.join(cwd, "pythonnative.json")
    requirements_path = os.path.join(cwd, "requirements.txt")
    gitignore_path = os.path.join(cwd, ".gitignore")

    # Prevent accidental overwrite unless --force is provided
    if not getattr(args, "force", False):
        exists = []
        if os.path.exists(app_dir):
            exists.append("app/")
        if os.path.exists(config_path):
            exists.append("pythonnative.json")
        if os.path.exists(requirements_path):
            exists.append("requirements.txt")
        if os.path.exists(gitignore_path):
            exists.append(".gitignore")
        if exists:
            print(f"Refusing to overwrite existing: {', '.join(exists)}. Use --force to overwrite.")
            sys.exit(1)

    os.makedirs(app_dir, exist_ok=True)

    # Minimal hello world app scaffold
    main_page_py = os.path.join(app_dir, "main_page.py")
    if not os.path.exists(main_page_py) or args.force:
        with open(main_page_py, "w", encoding="utf-8") as f:
            f.write(
                """import pythonnative as pn


class MainPage(pn.Page):
    def __init__(self, native_instance):
        super().__init__(native_instance)

    def on_create(self):
        super().on_create()
        stack = pn.StackView()
        stack.add_view(pn.Label("Hello from PythonNative!"))
        button = pn.Button("Tap me")
        button.set_on_click(lambda: print("Button clicked"))
        stack.add_view(button)
        self.set_root_view(stack)


def bootstrap(native_instance):
    '''Entry point called by the host app (Android Activity or iOS ViewController).'''
    page = MainPage(native_instance)
    page.on_create()
    return page
"""
            )

    # Create config
    config = {
        "name": project_name,
        "appId": "com.example." + project_name.replace(" ", "").lower(),
        "entryPoint": "app/main_page.py",
        "ios": {},
        "android": {},
    }
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # Requirements
    if not os.path.exists(requirements_path) or args.force:
        with open(requirements_path, "w", encoding="utf-8") as f:
            f.write("pythonnative\n")

    # .gitignore
    default_gitignore = "# PythonNative\n" "__pycache__/\n" "*.pyc\n" ".venv/\n" "build/\n" ".DS_Store\n"
    if not os.path.exists(gitignore_path) or args.force:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(default_gitignore)

    print("Initialized PythonNative project.")


def _copy_dir(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _copy_bundled_template_dir(template_dir: str, destination: str) -> None:
    """
    Copy a bundled template directory into the destination directory.
    Tries the repository `templates/` first during development, then
    package resources when installed from a wheel.
    The result should be `${destination}/{template_dir}`.
    """
    dest_path = os.path.join(destination, template_dir)

    # Dev-first: prefer local source templates if running from a checkout (avoid stale packaged data)
    try:
        # __file__ -> src/pythonnative/cli/pn.py, so go up to src/, then to repo root
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # Check templates located inside the source package tree
        local_pkg_templates = os.path.join(src_dir, "pythonnative", "templates", template_dir)
        if os.path.isdir(local_pkg_templates):
            _copy_dir(local_pkg_templates, dest_path)
            return
        repo_root = os.path.abspath(os.path.join(src_dir, ".."))
        repo_templates = os.path.join(repo_root, "templates")
        candidate_dir = os.path.join(repo_templates, template_dir)
        if os.path.isdir(candidate_dir):
            _copy_dir(candidate_dir, dest_path)
            return
    except Exception:
        pass

    # Try to load from installed package resources (templates packaged inside the module)
    try:
        cand = resources.files("pythonnative").joinpath("templates").joinpath(template_dir)
        with resources.as_file(cand) as p:
            resource_path = str(p)
            if os.path.isdir(resource_path):
                _copy_dir(resource_path, dest_path)
                return
    except Exception:
        pass

    # Last resort: check typical data-file locations
    try:
        data_paths = sysconfig.get_paths()
        search_bases = [
            data_paths.get("data"),
            data_paths.get("purelib"),
            data_paths.get("platlib"),
        ]
        for base in filter(None, search_bases):
            candidate_dir = os.path.join(base, "pythonnative", "templates", template_dir)
            if os.path.isdir(candidate_dir):
                _copy_dir(candidate_dir, dest_path)
                return
    except Exception:
        pass

    raise FileNotFoundError(f"Could not find bundled template directory {template_dir}. Ensure templates are packaged.")


def _github_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "pythonnative-cli"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def _resolve_python_apple_support_asset(
    py_major_minor: str = "3.11", preferred_name: str = "Python-3.11-iOS-support.b7.tar.gz"
) -> Optional[str]:
    """
    Find a browser_download_url for a Python-Apple-support asset on GitHub Releases.
    Prefers an exact name match (preferred_name). Falls back to the newest
    asset whose name contains "Python-{py_major_minor}-iOS-support" and endswith .tar.gz.
    """
    try:
        releases = _github_json("https://api.github.com/repos/beeware/Python-Apple-support/releases?per_page=100")
        # Search all releases for preferred_name first
        for rel in releases:
            for a in rel.get("assets", []) or []:
                name = a.get("name") or ""
                if name == preferred_name:
                    return a.get("browser_download_url")
        # Fallback: any matching Python-{version}-iOS-support*.tar.gz (take first encountered)
        needle = f"Python-{py_major_minor}-iOS-support"
        for rel in releases:
            for a in rel.get("assets", []) or []:
                name = a.get("name") or ""
                if needle in name and name.endswith(".tar.gz"):
                    return a.get("browser_download_url")
    except Exception:
        pass
    return None


def create_android_project(project_name: str, destination: str) -> None:
    """
    Create a new Android project using a template.

    :param project_name: The name of the project.
    :param destination: The directory where the project will be created.
    """
    # Copy the Android template project directory
    _copy_bundled_template_dir("android_template", destination)


def create_ios_project(project_name: str, destination: str) -> None:
    """
    Create a new iOS project using a template.

    :param project_name: The name of the project.
    :param destination: The directory where the project will be created.
    """
    # Copy the iOS template project directory
    _copy_bundled_template_dir("ios_template", destination)


def run_project(args: argparse.Namespace) -> None:
    """
    Run the specified project.
    """
    # Determine the platform
    platform: str = args.platform
    prepare_only: bool = getattr(args, "prepare_only", False)

    # Define the build directory
    build_dir: str = os.path.join(os.getcwd(), "build", platform)

    # Create the build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)

    # Generate the required project files
    if platform == "android":
        create_android_project("MyApp", build_dir)
    elif platform == "ios":
        create_ios_project("MyApp", build_dir)

    # Copy the user's Python code into the project
    src_dir: str = os.path.join(os.getcwd(), "app")

    # Adjust the destination directory for Android project
    if platform == "android":
        dest_dir: str = os.path.join(build_dir, "android_template", "app", "src", "main", "python", "app")
    else:
        # For iOS, stage the Python app in a top-level folder for later integration scripts
        dest_dir = os.path.join(build_dir, "app")

    # Create the destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)

    # During local development (running from repository), also bundle the
    # local library sources so the app uses the in-repo version instead of
    # the PyPI package. This provides faster inner-loop iteration and avoids
    # version skew during development.
    try:
        # __file__ -> src/pythonnative/cli/pn.py, so repo root is one up from src/
        src_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".."))
        local_lib = os.path.join(src_root, "pythonnative")
        if os.path.isdir(local_lib):
            if platform == "android":
                python_root = os.path.join(build_dir, "android_template", "app", "src", "main", "python")
            else:
                python_root = os.path.join(build_dir)  # staged at build/ios/app for iOS below
            os.makedirs(python_root, exist_ok=True)
            shutil.copytree(local_lib, os.path.join(python_root, "pythonnative"), dirs_exist_ok=True)
    except Exception:
        # Non-fatal; fallback to the packaged PyPI dependency if present
        pass

    # Install any necessary Python packages into the project environment
    # Skip installation during prepare-only to avoid network access and speed up scaffolding
    if not prepare_only:
        requirements_path = os.path.join(os.getcwd(), "requirements.txt")
        if os.path.exists(requirements_path):
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=False)

    # Run the project
    if prepare_only:
        print("Prepared project in build/ without building (prepare-only).")
        return

    if platform == "android":
        # Change to the Android project directory
        android_project_dir: str = os.path.join(build_dir, "android_template")
        os.chdir(android_project_dir)

        # Add executable permissions to the gradlew script
        gradlew_path: str = os.path.join(android_project_dir, "gradlew")
        os.chmod(gradlew_path, 0o755)  # this makes the file executable for the user

        # Build the Android project and install it on the device
        env: dict[str, str] = os.environ.copy()
        # Respect JAVA_HOME if set; otherwise, attempt a best-effort on macOS via Homebrew
        if sys.platform == "darwin" and not env.get("JAVA_HOME"):
            try:
                jdk_path: str = subprocess.check_output(["brew", "--prefix", "openjdk@17"]).decode().strip()
                env["JAVA_HOME"] = jdk_path
            except Exception:
                pass
        subprocess.run(["./gradlew", "installDebug"], check=True, env=env)

        # Run the Android app
        # Assumes that the package name of your app is "com.example.myapp" and the main activity is "MainActivity"
        # Replace "com.example.myapp" and ".MainActivity" with your actual package name and main activity
        subprocess.run(
            [
                "adb",
                "shell",
                "am",
                "start",
                "-n",
                "com.pythonnative.android_template/.MainActivity",
            ],
            check=True,
        )
    elif platform == "ios":
        # Attempt to build and run on iOS Simulator (best-effort)
        ios_project_dir: str = os.path.join(build_dir, "ios_template")
        if os.path.isdir(ios_project_dir):
            # Stage embedded Python runtime inputs by downloading pinned assets
            try:
                assets_dir = os.path.join(build_dir, "ios_runtime")
                os.makedirs(assets_dir, exist_ok=True)
                # Pinned preferred asset name and checksum (b7)
                preferred_name = "Python-3.11-iOS-support.b7.tar.gz"
                sha256 = "2b7d8589715b9890e8dd7e1bce91c210bb5287417e17b9af120fc577675ed28e"
                # Resolve a working download URL from GitHub Releases
                url = _resolve_python_apple_support_asset("3.11", preferred_name=preferred_name)
                if not url:
                    raise RuntimeError("Could not resolve Python-Apple-support asset URL from GitHub Releases.")
                tar_path = os.path.join(assets_dir, os.path.basename(url))
                if not os.path.exists(tar_path):
                    print("Downloading Python-Apple-support (3.11 iOS)")
                    req = urllib.request.Request(url, headers={"User-Agent": "pythonnative-cli"})
                    with urllib.request.urlopen(req) as r, open(tar_path, "wb") as f:
                        f.write(r.read())
                # Verify checksum
                h = hashlib.sha256()
                with open(tar_path, "rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
                if h.hexdigest() != sha256:
                    raise RuntimeError("SHA256 mismatch for Python-Apple-support tarball")
                # Extract only once
                extract_root = os.path.join(assets_dir, "extracted")
                if not os.path.isdir(extract_root):
                    os.makedirs(extract_root, exist_ok=True)
                    subprocess.run(["tar", "-xzf", tar_path, "-C", extract_root], check=True)
                # Provide Python.xcframework to the Xcode project and stdlib for bundling
                # Try both common layouts
                cand_frameworks = [
                    os.path.join(extract_root, "Python.xcframework"),
                    os.path.join(extract_root, "support", "Python.xcframework"),
                ]
                xc_src = next((p for p in cand_frameworks if os.path.isdir(p)), None)
                if xc_src:
                    shutil.copytree(xc_src, os.path.join(ios_project_dir, "Python.xcframework"), dirs_exist_ok=True)
                # Stdlib path
                cand_stdlib = [
                    os.path.join(extract_root, "Python.xcframework", "ios-arm64_x86_64-simulator", "lib", "python3.11"),
                    os.path.join(
                        extract_root, "support", "Python.xcframework", "ios-arm64_x86_64-simulator", "lib", "python3.11"
                    ),
                ]
                stdlib_src = next((p for p in cand_stdlib if os.path.isdir(p)), None)
            except Exception as e:
                print(f"Warning: failed to prepare Python runtime: {e}")

            os.chdir(ios_project_dir)
            derived_data = os.path.join(ios_project_dir, "build")
            try:
                # Detect a simulator UDID to target: prefer Booted; else any iPhone
                sim_udid: Optional[str] = None
                try:
                    import json as _json

                    devices_out = subprocess.run(
                        ["xcrun", "simctl", "list", "devices", "available", "--json"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    devs = _json.loads(devices_out.stdout or "{}").get("devices") or {}
                    all_devs = [d for lst in devs.values() for d in (lst or [])]
                    for d in all_devs:
                        if d.get("state") == "Booted":
                            sim_udid = d.get("udid")
                            break
                    if not sim_udid:
                        for d in all_devs:
                            if (d.get("isAvailable") or d.get("availability")) and (
                                d.get("name") or ""
                            ).lower().startswith("iphone"):
                                sim_udid = d.get("udid")
                                break
                except Exception:
                    pass

                xcode_dest = (
                    ["-destination", f"id={sim_udid}"] if sim_udid else ["-destination", "platform=iOS Simulator"]
                )

                # Provide header and lib paths for CPython (Simulator slice) ONLY if the
                # XCFramework is not already added to the Xcode project. When the project
                # contains `Python.xcframework`, Xcode manages headers and linking to avoid
                # duplicate module.modulemap definitions.
                extra_xcode_settings: list[str] = []
                try:
                    xc_present = os.path.isdir(os.path.join(ios_project_dir, "Python.xcframework"))
                    if not xc_present and "extract_root" in locals():
                        sim_headers = os.path.join(
                            extract_root, "Python.xcframework", "ios-arm64_x86_64-simulator", "Headers"
                        )
                        sim_lib = os.path.join(
                            extract_root, "Python.xcframework", "ios-arm64_x86_64-simulator", "libPython3.11.a"
                        )
                        if os.path.isdir(sim_headers):
                            extra_xcode_settings.extend(
                                [
                                    f"HEADER_SEARCH_PATHS={sim_headers}",
                                    f"SWIFT_INCLUDE_PATHS={sim_headers}",
                                ]
                            )
                        if os.path.exists(sim_lib):
                            extra_xcode_settings.append(f"OTHER_LDFLAGS=-force_load {sim_lib}")
                except Exception:
                    pass

                subprocess.run(
                    [
                        "xcodebuild",
                        "-project",
                        "ios_template.xcodeproj",
                        "-scheme",
                        "ios_template",
                        "-configuration",
                        "Debug",
                        *xcode_dest,
                        "-derivedDataPath",
                        derived_data,
                        "build",
                        *extra_xcode_settings,
                    ],
                    check=False,
                )
            except FileNotFoundError:
                print("xcodebuild not found. Skipping iOS build step.")
                return

            # Locate built app
            app_path = os.path.join(derived_data, "Build", "Products", "Debug-iphonesimulator", "ios_template.app")
            if not os.path.isdir(app_path):
                print("Could not locate built .app; open the project in Xcode to run.")
                return

            # Copy staged Python app and optional embedded runtime into the .app bundle
            try:
                staged_app_src = os.path.join(build_dir, "app")
                if os.path.isdir(staged_app_src):
                    shutil.copytree(staged_app_src, os.path.join(app_path, "app"), dirs_exist_ok=True)
                # Also copy local library sources if present for dev flow
                src_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".."))
                local_lib = os.path.join(src_root, "pythonnative")
                if os.path.isdir(local_lib):
                    shutil.copytree(local_lib, os.path.join(app_path, "pythonnative"), dirs_exist_ok=True)
                # Copy stdlib from downloaded support if available
                if "stdlib_src" in locals() and stdlib_src and os.path.isdir(stdlib_src):
                    shutil.copytree(stdlib_src, os.path.join(app_path, "python-stdlib"), dirs_exist_ok=True)
                # Embed Python.framework for Simulator so PythonKit can dlopen it (from downloaded XCFramework)
                sim_fw = None
                if "extract_root" in locals():
                    cand_fw = [
                        os.path.join(
                            extract_root, "Python.xcframework", "ios-arm64_x86_64-simulator", "Python.framework"
                        ),
                        os.path.join(
                            extract_root,
                            "support",
                            "Python.xcframework",
                            "ios-arm64_x86_64-simulator",
                            "Python.framework",
                        ),
                    ]
                    sim_fw = next((p for p in cand_fw if os.path.isdir(p)), None)
                fw_dest_dir = os.path.join(app_path, "Frameworks")
                os.makedirs(fw_dest_dir, exist_ok=True)
                if sim_fw and os.path.isdir(sim_fw):
                    shutil.copytree(sim_fw, os.path.join(fw_dest_dir, "Python.framework"), dirs_exist_ok=True)
                # Install rubicon-objc into platform-site

                # Ensure importlib.metadata finds package metadata for rubicon-objc by
                # installing it into a site-like dir that is on sys.path (platform-site).
                try:
                    tmp_site = os.path.join(build_dir, "ios_site")
                    if os.path.isdir(tmp_site):
                        shutil.rmtree(tmp_site)
                    os.makedirs(tmp_site, exist_ok=True)
                    # Install pure-Python rubicon-objc distribution metadata and package
                    subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--no-deps",
                            "--upgrade",
                            "rubicon-objc",
                            "-t",
                            tmp_site,
                        ],
                        check=False,
                    )
                    platform_site_dir = os.path.join(app_path, "platform-site")
                    os.makedirs(platform_site_dir, exist_ok=True)
                    for entry in os.listdir(tmp_site):
                        src_entry = os.path.join(tmp_site, entry)
                        dst_entry = os.path.join(platform_site_dir, entry)
                        if os.path.isdir(src_entry):
                            shutil.copytree(src_entry, dst_entry, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src_entry, dst_entry)
                except Exception:
                    # Non-fatal; if metadata isn't present, rubicon import may fail and fallback UI will appear
                    pass
                # Note: Python.xcframework provides a static library for Simulator; it must be linked at build time.
                # We copy the XCFramework into the project directory above so Xcode can link it.
            except Exception:
                # Non-fatal; fallback UI will appear if import fails
                pass

            # Find an available simulator and boot it
            try:
                import json as _json

                result = subprocess.run(
                    ["xcrun", "simctl", "list", "devices", "available", "--json"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                devices_json = _json.loads(result.stdout or "{}")
                all_devices: List[Dict[str, Any]] = []
                for _runtime, devices in (devices_json.get("devices") or {}).items():
                    all_devices.extend(devices or [])
                # Prefer iPhone 15/15 Pro names; else first available iPhone
                preferred = None
                for d in all_devices:
                    name = (d.get("name") or "").lower()
                    if "iphone 15" in name and d.get("isAvailable"):
                        preferred = d
                        break
                if not preferred:
                    for d in all_devices:
                        if d.get("isAvailable") and (d.get("name") or "").lower().startswith("iphone"):
                            preferred = d
                            break
                if not preferred:
                    print("No available iOS Simulators found; open the project in Xcode to run.")
                    return

                udid = preferred.get("udid")
                # Boot (no-op if already booted)
                subprocess.run(["xcrun", "simctl", "boot", udid], check=False)
                # Install and launch
                subprocess.run(["xcrun", "simctl", "install", udid, app_path], check=False)
                subprocess.run(["xcrun", "simctl", "launch", udid, "com.pythonnative.ios-template"], check=False)
                print("Launched iOS app on Simulator (best-effort).")
            except Exception:
                print("Failed to auto-run on Simulator; open the project in Xcode to run.")


def clean_project(args: argparse.Namespace) -> None:
    """
    Clean the specified project.
    """
    # Define the build directory
    build_dir: str = os.path.join(os.getcwd(), "build")

    # Check if the build directory exists
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print("Removed build/ directory.")
    else:
        print("No build/ directory to remove.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="pn", description="PythonNative CLI")
    subparsers = parser.add_subparsers()

    # Create a new command 'init' that calls init_project
    parser_init = subparsers.add_parser("init")
    parser_init.add_argument("name", nargs="?", help="Project name (defaults to current directory name)")
    parser_init.add_argument("--force", action="store_true", help="Overwrite existing files if present")
    parser_init.set_defaults(func=init_project)

    # Create a new command 'run' that calls run_project
    parser_run = subparsers.add_parser("run")
    parser_run.add_argument("platform", choices=["android", "ios"])
    parser_run.add_argument(
        "--prepare-only",
        action="store_true",
        help="Extract templates and stage app without building",
    )
    parser_run.set_defaults(func=run_project)

    # Create a new command 'clean' that calls clean_project
    parser_clean = subparsers.add_parser("clean")
    parser_clean.set_defaults(func=clean_project)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
