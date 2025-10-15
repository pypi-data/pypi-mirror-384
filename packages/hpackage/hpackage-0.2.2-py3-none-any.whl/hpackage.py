#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-SideFX-EULA
import argparse
import base64
import collections
import configparser
import datetime
import functools
import glob
import hashlib
import itertools
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import textwrap
import time
import urllib
import webbrowser
import zipfile
from email.utils import parsedate_to_datetime
from pathlib import Path


if sys.version_info < (3, 8):
    sys.exit("Error: Python 3.8+ is required.")

try:
    import requests
except ImportError:
    sys.exit("This program requires Python's requests module. Please run:\n"
        "    pip install requests")


CHUNK_SIZE = 65536


class Options:
    def __init__(self):
        self.verbosity = (
            2 if os.environ.get("HOUDINI_PACKAGE_VERBOSE", "0") == "0" else 3)
        self.server = os.environ.get(
            "HOUDINI_PACKAGE_SERVER", "https://www.sidefx.com")
        self.timeout = 30
        self.authentication = None

    def find_authentication(self, force=False, find_all=False):
        if not self.authentication or force:
            self.authentication = _find_authentication(find_all=find_all)
        return self.authentication

    def require_authentication(self):
        self.authentication = self.find_authentication()
        if self.authentication is None:
            print_error("You are not logged in", exit=True)
        return self.authentication


OPTIONS = Options()


def create_parser():
    parser = argparse.ArgumentParser(prog="hpackage")
    parser.add_argument(
        "-v", "--verbosity", default="2",
        help="set the verbosity level (2 by default)")
    parser.add_argument(
        "--timeout", help="set the connection timeout in seconds")
    parser.add_argument("--server", help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command", required=True)

    # auth subcommand:
    auth_parser = subparsers.add_parser("auth", help="authentication commands")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_cmd", required=True)
    auth_subparsers.add_parser("login", help="log in via a browser")
    auth_subparsers.add_parser("logout", help="log out")
    auth_subparsers.add_parser("status", help="show authentication status")
    auth_subparsers.add_parser("installkey",
        help="install an API key, generating it if necessary")
    uninstallkey_parser = auth_subparsers.add_parser("uninstallkey",
        help="delete the local API key, keeping it on sidefx.com")
    uninstallkey_parser.add_argument(
        "client_id", metavar="CLIENT-ID",
        help="client id of the key to uninstall")
    deletekey_parser = auth_subparsers.add_parser("deletekey",
        help="delete the local API key and delete it from sidefx.com")
    deletekey_parser.add_argument(
        "client_id", metavar="CLIENT-ID",
        help="client id of the key to delete")

    # install subcommand:
    install_parser = subparsers.add_parser("install", help="install packages")
    install_parser.add_argument(
        "-U", "--upgrade",
        help="upgrade the specified package to the latest version")
    install_parser.add_argument(
        "-r", "--requirements", metavar="FILE",
        help="install all packages listed in the given requirements file")
    install_parser.add_argument(
        "--force-reinstall", action="store_true",
        help="force a reinstall of the specified package")
    install_parser.add_argument(
        "package_spec", nargs="?",
        help="package specification to install (e.g. pkg or pkg==1.2.3)")

    # uninstall subcommand:
    uninstall_parser = subparsers.add_parser(
        "uninstall", help="uninstall a package")
    uninstall_parser.add_argument(
        "package",
        help="name of the package to uninstall")
    uninstall_parser.add_argument(
        "-y", "--yes", action="store_true",
        help="answer yes when asked to break dependencies")

    # list subcommand:
    list_parser = subparsers.add_parser("list", help="list installed packages")
    list_parser.add_argument(
        "--show-location", action="store_true",
        help="show the location of each package")
    list_parser.add_argument(
        "--show-dependencies", action="store_true",
        help="show the dependencies of each package")
    list_parser.add_argument(
        "package_name", nargs="*",
        help="optional package names")

    # author subcommand:
    author_parser = subparsers.add_parser(
        "author", help="author a package")
    author_subparsers = author_parser.add_subparsers(
        dest="author_cmd", required=True)
    reserve_parser = author_subparsers.add_parser(
        "reserve", help="reserve a package name and create zip file")
    reserve_parser.add_argument(
        "package", help="a package name")
    reserve_parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="run in interactive mode, prompting for input")
    verifyjson_parser = author_subparsers.add_parser(
        "verifyjson", help="verify a package json file")
    verifyjson_parser.add_argument(
        "package", help="a package name or path to a json file")
    upload_parser = author_subparsers.add_parser(
        "upload", help="upload a package")
    upload_parser.add_argument(
        "package",
        help="a package name or path")
    upload_parser.add_argument(
        "--requires-grant", action="store_true",
        help="require access to be granted to download the package")
    upload_parser.add_argument(
        "--auto-publish", action="store_true",
        help="automatically publish after review completes")
    getstatus_parser = author_subparsers.add_parser(
        "getstatus", help="get the status of your package")
    getstatus_parser.add_argument(
        "package", help="a package name")
    grant_parser = author_subparsers.add_parser(
        "grant", help="grant access to a package")
    grant_parser.add_argument(
        "package", help="name of the package for which to grant access")
    grant_parser.add_argument(
        "emails", nargs="+",
        help="one or more email addresses to grant access to")
    publish_parser = author_subparsers.add_parser(
        "publish", help="publish a package to make it accessible")
    publish_parser.add_argument(
        "package", help="a package name or path")
    unpublish_parser = author_subparsers.add_parser(
        "unpublish", help="unpublish a package")
    unpublish_parser.add_argument(
        "package_and_version", help="In the form <name>==<version>")
    delete_parser = author_subparsers.add_parser(
        "delete", help="delete a package")
    delete_parser.add_argument(
        "package_and_version", help="In the form <name>==<version>")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        OPTIONS.verbosity = int(args.verbosity)
    except ValueError:
        print_error("Invalid verbosity level")

    if args.server:
        OPTIONS.server = args.server
        while OPTIONS.server.endswith("/"):
            OPTIONS.server = OPTIONS.server[:-1]
    if args.timeout:
        try:
            OPTIONS.timeout = int(args.timeout)
        except ValueError:
            print_error("The timeout is not an integer")

    # Dispatch to the appropriate handler
    if args.command == "auth":
        if args.auth_cmd == "login":
            log_in()
        elif args.auth_cmd == "logout":
            logout()
        elif args.auth_cmd == "status":
            print_auth_status()
        elif args.auth_cmd == "installkey":
            create_and_install_oauth2_keys()
        elif args.auth_cmd == "uninstallkey":
            uninstall_oauth2_keys(args.client_id)
        elif args.auth_cmd == "deletekey":
            uninstall_and_delete_oauth2_keys(args.client_id)
    elif args.command == "install":
        if args.upgrade:
            upgrade(args.upgrade)
        elif args.requirements:
            install_from_requirements(args.requirements)
        elif args.package_spec:
            install(args.package_spec, force_reinstall=args.force_reinstall)
        else:
            parser.error("install requires a package specification")
    elif args.command == "uninstall":
        uninstall(args.package, skip_prompt=args.yes)
    elif args.command == "list":
        list_packages(args.package_name, show_location=args.show_location,
            show_dependencies=args.show_dependencies)
    elif args.command == "author":
        if args.author_cmd == "reserve":
            reserve_upload(args.package, args.interactive)
        elif args.author_cmd == "verifyjson":
            verify_package_json(args.package)
        elif args.author_cmd == "upload":
            upload(args.package, requires_grant=args.requires_grant,
                auto_publish=args.auto_publish)
        elif args.author_cmd == "getstatus":
            get_status_for_author(args.package)
        elif args.author_cmd == "grant":
            grant(args.package, args.emails)
        elif args.author_cmd == "publish":
            publish(args.package)
        elif args.author_cmd == "unpublish":
            unpublish(args.package_and_version)
        elif args.author_cmd == "delete":
            delete(args.package_and_version)


def log_in(print_status=True):
    authentication = OPTIONS.find_authentication()
    if authentication is not None and authentication.session_id:
        print_error("You are already logged in", exit=False)
        print_auth_status()
        sys.exit(1)

    webbrowser.open(f"{OPTIONS.server}/login/launcher/", new=2)
    print("Waiting for you to log in via a browser (press Ctrl+C to quit)")
    time.sleep(1)
    while True:
        session_id, _csrf_token = _get_session_id_from_hserver(
            require_hserver_running=True)
        if session_id:
            break
        time.sleep(5)

    if print_status:
        # Clear the authentication so we re-find it, otherwise we might use
        # OAuth2 keys instead of the session id.
        OPTIONS.find_authentication(force=True, find_all=True)
        print_auth_status()


def logout():
    authentication = OPTIONS.find_authentication(find_all=True)
    if authentication.session_id:
        _call_hserver("cmd_del_session", method="PUT", require_json=False,
            domain=_get_cookie_domain())

    if authentication.client_id:
        print_warning("Note that you are still logged in via"
            f" {authentication.method_name()}")


def print_auth_status():
    authentication = OPTIONS.find_authentication(find_all=True)
    if not authentication:
        print("You are not logged in")
        return
    for name, label in (
            ("username", "username"),
            ("email", "email"),
            ("company_name", "company")):
        print(f"{label:<14}: {authentication.validation_output.get(name)}")
    print(f"{'Login method':<14}: {authentication.method_name()}")
    if authentication.client_id:
        print(f"{'API client id':<14}: {authentication.client_id}")


def create_and_install_oauth2_keys():
    authentication = OPTIONS.find_authentication()
    if authentication is None:
        log_in(print_status=False)
        authentication = OPTIONS.require_authentication()
    elif authentication.client_id:
        print_error("You are already using an API key")

    application = _post_to_sidefx(
        "/oauth2/find-or-create-application/", authentication,
        {"name": "hpackage keys"}).json()

    for path in _find_hserver_ini_paths(os.W_OK):
        with path.open("a") as open_file:
            open_file.write(
                f"ClientID = {application['client_id']}\n"
                f"ClientSecret = {application['client_secret']}\n")
        break
    else:
        print_error("You do not have permission to write any hserver.ini files")


def uninstall_oauth2_keys(client_id):
    path = None
    for cur_path in _find_hserver_ini_paths(os.W_OK):
        lines = cur_path.read_text().splitlines()
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line.startswith("ClientID"):
                continue
            parts = [part.strip() for part in stripped_line.split("=")]
            if len(parts) == 2 and parts[-1] == client_id:
                path = cur_path
                client_id_line_index = i
                break

        if path is not None:
            break

    if path is None:
        print_error("This client id is not installed")

    with path.open("w") as open_file:
        removed_client_secret = False
        for i, line in enumerate(lines):
            if i == client_id_line_index:
                continue
            if (not removed_client_secret and i > client_id_line_index and
                    line.strip().startswith("ClientSecret")):
                removed_client_secret = True
                continue

            open_file.write(line + "\n")


def uninstall_and_delete_oauth2_keys(client_id):
    authentication = OPTIONS.require_authentication()
    _post_to_sidefx(
        "/oauth2/delete-application/", authentication,
        {"client_id": client_id})
    uninstall_oauth2_keys(client_id)


def _parse_package_and_version(package_name_and_optional_version):
    parts = package_name_and_optional_version.split("==", 1)
    if len(parts) == 1:
        return parts[0], None

    return parts[0], parts[1]


def install(package_name, force_reinstall=False, installation_dir=None):
    authentication = OPTIONS.find_authentication()
    package_name, version, info = _get_package_info_from_name(
        package_name, authentication)

    houdini_major_minor = _houdini_major_minor()
    if Version(houdini_major_minor) < Version(info["min_houdini_major_minor"]):
        print_error(f"{package_name}=={version} requires at least Houdini"
            f" {info['min_houdini_major_minor']} and is not compatible with"
            f" Houdini {houdini_major_minor}")

    # Uninstall if we're upgrading/forcing reinstallation.
    installed_packages = _installed_packages()
    installed_info = installed_packages.get(package_name)
    if (installed_info and installed_info["version"] == version and
            not force_reinstall):
        print_error(f"{package_name}=={version} is already installed.")

    # Check dependencies.
    dependencies_to_install = []
    for dependency in info.get("depends_on", []):
        dep_name = dependency["name"]
        dep_min_version = dependency.get("min_version", None)
        dep_max_version = dependency.get("max_version", None)
        dep_installed_info = installed_packages.get(dep_name)
        if dep_installed_info is None:
            # TODO: What if dep_max_version doesn't exist?  If not, find the
            #       version closest to it.
            if dep_max_version:
                dependencies_to_install.append(
                    f"{dep_name}=={dep_max_version}")
            else:
                dependencies_to_install.append(dep_name)
        else:
            dep_installed_version = dep_installed_info["version"]
            if (dep_max_version and
                    Version(dep_max_version) < Version(dep_installed_version)):
                print_error(
                    f"{package_name}=={version} requires"
                    f" {dep_name}<={dep_max_version}"
                    f" but {dep_installed_version} is installed")
            if (dep_min_version and
                    Version(dep_installed_version) < Version(dep_min_version)):
                print_error(
                    f"{package_name}=={version} requires"
                    f" {dep_name}>={dep_min_version}"
                    f" but {dep_installed_version} is installed")

    # Install dependencies as necessary.
    for dependency_to_install in dependencies_to_install:
        if OPTIONS.verbosity > 0:
            print(f"Installing {dependency_to_install}")
        install(dependency_to_install, installation_dir=installation_dir)

    # See if this package requires a grant.
    if not info["requires_grant"]:
        url = f"{OPTIONS.server}/hpack/download/{package_name}/{version}.zip"
    else:
        if authentication is None:
            authentication = OPTIONS.require_authentication()
        url = _call_sidefx("hpack.get_download_url_with_grant",
            authentication, authentication.email(), package_name,
            version=version)

    if installed_info:
        _uninstall_ignoring_dependencies(package_name)

    if installation_dir is None:
        installation_dir = Path(_houdini_user_pref_dir()) / "packages"
    installation_dir.mkdir(parents=True, exist_ok=True)

    zip_path = installation_dir / f"{package_name}-{version}.zip"
    _download_file(authentication, url, zip_path, f"{package_name}=={version}",
        info["file_size"], info["md5_checksum"],
        print_progress=OPTIONS.verbosity > 0)
    _extract_zip(zip_path, installation_dir)
    zip_path.unlink()


def _get_package_info_from_name(package_name, authentication):
    package_name, version = _parse_package_and_version(package_name)
    if version is None:
        version = _call_sidefx("hpack.get_latest_package_version",
            authentication, package_name)

    # Note that fetching the dependencies will validate that the package
    # version exists.
    return package_name, version, _call_sidefx(
        "hpack.get_info_to_install_package",
        authentication, package_name, version)


def install_from_requirements(requirements_path):
    path = Path(requirements_path)
    if not path.is_file():
        print_error(f"{requirements_path} is not a valid file")

    package_names = [line.strip() for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")]
    for package_name in package_names:
        install(package_name)


def upgrade(package_name):
    # Parse the name==version or get the latest version.
    authentication = OPTIONS.find_authentication()
    package_name, version, _info = _get_package_info_from_name(
        package_name, authentication)

    # Make sure the package is installed and it's not already at this version.
    installed_info = _installed_packages().get(package_name)
    if installed_info is None:
        print_error(f"{package_name} is not installed")

    if installed_info.get("version") == version:
        print_error(f"{package_name}=={version} is already installed and"
            " is the latest version")

    # Uninstall the old version and install the new one.
    installation_dir = None
    if installed_info:
        installation_dir = Path(installed_info["location"]).parent
        _uninstall_ignoring_dependencies(package_name)

    install(f"{package_name}=={version}", installation_dir=installation_dir)


def uninstall(package_name, skip_prompt):
    package_name, version = _parse_package_and_version(package_name)

    installed_packages = _installed_packages()
    installed_info = installed_packages.get(package_name)
    if installed_info is None:
        print_error(f"{package_name} is not installed")

    if version is not None and installed_info["version"] != version:
        print_error(
            f"{package_name}=={installed_info['version']} is installed,"
            f" not version {version}")

    dependencies = _calculate_dependencies(installed_packages)
    needed_by = dependencies[package_name]["needed_by"]
    if needed_by:
        print_warning(f"{package_name} is needed by:" + "".join(
            "\n    " + other_package_name
            for other_package_name in sorted(needed_by)))
        if not skip_prompt:
            if not _prompt("Are you sure you want to continue", False):
                sys.exit(1)

    _uninstall_ignoring_dependencies(package_name, installed_info)


def _calculate_dependencies(installed_packages=None):
    if installed_packages is None:
        installed_packages = _installed_packages()

    # Calculate direct dependencies.  If they have local/edited package
    # requirements on things that don't exist, skip them.
    direct_dependencies = {
        package_name: set() for package_name in installed_packages}
    for package_name, installed_info in installed_packages.items():
        for requirement in installed_info["requires"]:
            dependency_name = requirement["name"]
            if dependency_name in installed_packages:
                direct_dependencies[package_name].add(dependency_name)
            else:
                print_warning(
                    f"{package_name} depends on {dependency_name} but it is"
                    " not installed")

    # Now calculate indirect dependencies.  First use Kahn's algorithm to sort
    # topologically so that we process parents (what has the dependency)
    # before children (the thing it depends on).
    indegrees = {package_name: 0 for package_name in installed_packages}
    for dependencies in direct_dependencies.values():
        for dependency_name in dependencies:
            indegrees[dependency_name] += 1

    # Walk down from toplevel dependencies to build the topography.
    queue = collections.deque([
        package_name for package_name, degree in indegrees.items()
        if degree == 0])
    topo = []
    while queue:
        package_name = queue.popleft()
        topo.append(package_name)
        for dependency_name in direct_dependencies[package_name]:
            indegrees[dependency_name] -= 1
            if indegrees[dependency_name] == 0:
                queue.append(dependency_name)

    if len(topo) != len(installed_packages):
        # TODO: Run "list --show-modifications" to show them what they've
        #       changed or what hasn't been added.
        print_error("Cycle detected in package dependencies.  Please check"
            " 'requires' in the packages you are authoring.")

    # Compute the transitive closures in reverse topological order.
    depends_on = {package_name: set() for package_name in installed_packages}
    for package_name in reversed(topo):
        closure = depends_on[package_name]
        for dependency_name in direct_dependencies[package_name]:
            closure.add(dependency_name)
            closure |= depends_on[dependency_name]

    # Now calculate reverse dependencies, including both direct and indirect.
    needed_by = {package_name: set() for package_name in installed_packages}
    for package_name, dependencies in depends_on.items():
        for dependency_name in dependencies:
            needed_by[dependency_name].add(package_name)

    return {
        package_name: {
            "directly_depends_on": direct_dependencies[package_name],
            "depends_on": depends_on[package_name],
            "needed_by": needed_by[package_name],
        } for package_name in installed_packages}


def _uninstall_ignoring_dependencies(package_name, installed_info=None):
    if installed_info is None:
        installed_info = _installed_packages().get(package_name)

    installed_info["location"].with_suffix(".json").unlink()
    shutil.rmtree(installed_info["location"])


def list_packages(package_names, show_location, show_dependencies):
    # TODO: Add a "show-modifications" to show which packages have json that's
    #       been changed from what's saved to the server, or to show them what
    #       hasn't been uploaded to the server.  Store checksums in the
    #       package json (one for the json, one for the dir contents) so we
    #       don't have to make a call to the server for each one.
    package_names = (set(package_names) if package_names else None)

    installed_packages = _installed_packages()
    if show_dependencies:
        dependencies = _calculate_dependencies(installed_packages)

    max_len = max(
        (len(package_name) + 2 + len(info["version"])
        for package_name, info in installed_packages.items()), default=0)
    for package_name, info in sorted(installed_packages.items()):
        if package_names and package_name not in package_names:
            continue
        line = f"{package_name}=={info['version']}"
        if show_location:
            line += " " * (max_len + 2 - len(line))
            line += str(info["location"])
        print(line)
        if show_dependencies:
            for dependency_name in dependencies[
                    package_name]["directly_depends_on"]:
                print("    -", dependency_name)


def reserve_upload(package, interactive):
    authentication = OPTIONS.require_authentication()

    user_pref_dir = _houdini_user_pref_dir()
    if user_pref_dir is None:
        print_error("No installed Houdini version could be detected, is it"
            " installed?")

    packages_dir = Path(user_pref_dir) / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)
    package_dir = packages_dir / package
    package_json = package_dir.with_suffix(".json")

    if package_json.exists() or package_dir.exists():
        print_warning(
            "You already have a package with this name so no example"
            " package will be created.  Move aside the existing package to"
            " create an example.")
        _validate_package_json(package_json)
        return

    if interactive:
        readme_markdown = input(
            "Enter a short one-line readme description:\n") + "\n"

    zip_contents = _call_sidefx("hpack.reserve_package_name",
        authentication, package, _houdini_major_minor())
    with zipfile.ZipFile(io.BytesIO(zip_contents), "r") as zip_file:
        zip_file.extractall(packages_dir)
    print(f"Created {package_dir}")

    getting_started_path = package_dir / "getting-started.txt"
    if interactive:
        (package_dir / "README.md").write_text(readme_markdown)
        print(getting_started_path.read_text())
        if _prompt("Delete getting-started.txt?", default_to_y=True):
            getting_started_path.unlink()
    else:
        print(f"\nSee {getting_started_path} for instructions.")



def verify_package_json(package_name_or_path):
    json_path = _find_package_json_path(package_name_or_path)
    if OPTIONS.verbosity > 0:
        print(f"{json_path} is valid")


def upload(package_name_or_path, requires_grant, auto_publish):
    authentication = OPTIONS.require_authentication()

    # TODO: Only read the first, say, 10K of any file (package json, README.md,
    #       etc) in order to prevent attacks that try to fill up the server's
    #       memory.

    json_path = _find_package_json_path(package_name_or_path)
    package_name = json_path.with_suffix("").stem

    if os.path.exists(json_path.with_suffix("") / "getting-started.txt"):
        print_error(
            "Please perform the actions in getting-started.txt and then"
            " delete this file.")

    readme_md_path = _find_readme_md_path(json_path)
    if "<enter a one-line description" in readme_md_path.read_text():
        print_error(
            "Please edit {readme_md_path} and add a description.")

    zip_path = _create_zipfile(json_path)
    try:
        file_size = zip_path.stat().st_size
        upload_info = _call_sidefx("hpack.start_upload", authentication,
            json.loads(json_path.read_text()), readme_md_path.read_text(),
            file_size, _compute_md5_checksum(zip_path),
            requires_grant=requires_grant, auto_publish=auto_publish)

        # Resume a partially complete upload if possible.
        uploaded = upload_info["partial_upload_size"]
        if (uploaded and _compute_md5_checksum(zip_path, uploaded) ==
                upload_info["partial_upload_md5_checksum"]):
            index = uploaded
        else:
            index = 0

        with zip_path.open("rb") as open_file:
            open_file.seek(index)
            while True:
                data = open_file.read(CHUNK_SIZE)
                if not data:
                    break
                result = _call_sidefx("hpack.upload_chunk", authentication,
                    upload_info["token"], index, data=bytearray(data))
                index += len(data)

                assert result["uploaded"] == index
                assert result["expecting"] == file_size

                if OPTIONS.verbosity > 0:
                    _print_progress_bar(
                        index / file_size, suffix=f"uploading {package_name}")
        if OPTIONS.verbosity > 0:
            message = f"\rSuccessfully uploaded {package_name}"
            print(f"{message:<{_num_terminal_cols()}}")
    finally:
        zip_path.unlink()

    print(f"{OPTIONS.server}/hpack/package/{package_name}")


def _compute_md5_checksum(file_path, only_first_bytes=None):
    infinity = 1 << 63    # effectively infinite
    hasher = hashlib.md5()
    with open(file_path, "rb") as open_file:
        remain = only_first_bytes if only_first_bytes is not None else infinity
        while remain > 0:
            b = open_file.read(min(CHUNK_SIZE, remain))
            if not b:
                break
            hasher.update(b)
            remain -= len(b)
    return hasher.hexdigest()


def _find_readme_md_path(json_path):
    readme_md_path = json_path.with_suffix("") / "README.md"
    if not readme_md_path.is_file():
        print_error(f"You need to create {readme_md_path} and put a package"
            " description there.")
    return readme_md_path


def _create_zipfile(json_path):
    package_dir = json_path.with_suffix("")
    parent_dir = json_path.parent

    package_name = json_path.stem
    zip_path = parent_dir / (package_name + ".zip")

    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.write(json_path, arcname=json_path.relative_to(parent_dir))

        for subpath in itertools.chain(
                package_dir.rglob("*"), package_dir.rglob(".*")):
            archive_path = Path(subpath).relative_to(parent_dir)
            if subpath.is_dir():
                _mkdir_in_zipfile(zip_file, archive_path)
            elif subpath.is_file():
                zip_file.write(subpath, arcname=archive_path)

    return zip_path


def _mkdir_in_zipfile(zip_file, dir_path):
    # Note that zipfile.mkdir was not added until Python 3.11.
    dir_path = str(dir_path)
    if not dir_path.endswith("/"):
        dir_path += "/"
    dir_info = zipfile.ZipInfo(dir_path)
    dir_info.date_time = time.localtime()[:6]
    dir_info.external_attr = (stat.S_IFDIR | 0o755) << 16
    zip_file.writestr(dir_info, "")


def _find_package_json_path(package_name_or_path):
    if package_name_or_path.endswith(".json"):
        json_path = package_name_or_path
    elif "/" in package_name_or_path or os.path.exists(
            package_name_or_path + ".json"):
        json_path = package_name_or_path + ".json"
    else:
        # Treat the path as a package name.
        json_path = None
        user_pref_dir = _houdini_user_pref_dir()
        if user_pref_dir:
            json_path = (Path(user_pref_dir) / "packages" /
                (package_name_or_path + ".json"))
            if not json_path.is_file():
                json_path = None

        if json_path is None:
            print_error(f"{package_name_or_path} is not a package json file")

    if not _validate_package_json(json_path):
        sys.exit(1)

    return Path(json_path)


def _validate_package_json(json_path):
    json_path = Path(json_path)
    if not json_path.exists():
        print_error(f"{json_path} does not exist", exit=False)
        return False
    if not json_path.is_file():
        print_error(f"{json_path} is not a file", exit=False)
        return False

    try:
        contents = json_path.read_text()
    except (PermissionError, OSError):
        print_error(f"{json_path} could not be read", exit=False)
        return False

    try:
        j = json.loads(contents)
    except json.JSONDecodeError as e:
        print_error(f"{json_path} does not contain valid JSON data\n{e}",
            exit=False)
        return False

    if not isinstance(j, dict):
        print_error(f"{json_path} does not contain a JSON object",
            exit=False)
        return False

    if "env" not in j:
        print_error(f'{json_path} does not contain an "env" entry',
            exit=False)
        return False

    if not isinstance(j["env"], (list, dict)):
        print_error(
            f'In {json_path}, "env" should be an array or an object',
            exit=False)
        return False

    if "hpack" not in j:
        print_error(f'{json_path} does not contain an "hpack" entry',
            exit=False)
        return False

    if not isinstance(j["hpack"], dict):
        print_error(f'In {json_path}, "hpack" should be a JSON object',
            exit=False)
        return False

    if "version" not in j["hpack"]:
        print_error(
            f'In {json_path}, "hpack" does not contain a "version" entry',
            exit=False)
        return False

    version = j["hpack"]["version"]
    if not isinstance(version, str):
        print_error(f'In {json_path}, "version" should be a string',
            exit=False)
        return False

    try:
        Version(version)
    except ValueError:
        print_error(f'In {json_path}, "{version}" is not a valid'
            ' version number', exit=False)
        return False

    orig_version = version
    version = str(Version(version))
    if orig_version != version:
        print_error(f'In {json_path}, shorten "{orig_version}" to "{version}"',
            exit=False)

    if isinstance(j["env"], dict):
        env_dict = j["env"]
    else:
        env_dict = {}
        for sub_dict in j["env"]:
            env_dict.update(sub_dict)

    package_name = Path(json_path).stem
    is_valid = True
    for d, name, expected in (
                (j, "name", package_name),
                (env_dict, f"PKG_{package_name.upper()}",
                    f"$HOUDINI_PACKAGE_PATH/{package_name}"),
                (j, "hpath", f"$HOUDINI_PACKAGE_PATH/{package_name}/houdini"),
                (j, "load_package_once", True),
                (j, "show", True),
            ):
        actual = d.get(name)
        if actual != expected:
            print_error(f'In {json_path}, "{name}" should be "{expected}",'
                f' not {actual}', exit=False)
            is_valid = False

    # Make sure they specify a minimum Houdini version.
    minimum_houdini_major_minor = (
        _extract_houdini_major_minor_from_enable_value(
            json_path, j.get("enable", {})))
    if minimum_houdini_major_minor is None:
        print_error(f'In {json_path}, there is not an "enable" entry defining a'
            ' strictly minimum Houdini version such as:\n'
            '"houdini_version >= \'21.0\'"',
            exit=False)
        is_valid = False

    requires = j.get("requires")
    if requires is not None:
        if not isinstance(requires, list):
            print_error(
                f'In {json_path}, "requires" is not an array', exit=False)
            is_valid = False
        else:
            for requires_name in requires:
                if not isinstance(requires_name, str):
                    print_error(
                        f'In {json_path}, invalid element {requires_name!r} in'
                        ' "requires"', exit=False)
                    is_valid = False

    for key in ("min_versions", "max_versions"):
        versions = j["hpack"].get(key)
        if versions is None:
            continue
        if not isinstance(versions, dict):
            print_error(
                f'In {json_path}, "{key}" is not a JSON object', exit=False)
            is_valid = False
            continue
        for name, version_str in j["hpack"][key].items():
            if not isinstance(name, str) or not isinstance(version_str, str):
                print_error(
                    f'In {json_path}, "{key}" entries must be strings',
                    exit=False)
                is_valid = False
            elif name not in requires:
                print_error(
                    f'In {json_path}, "{name}" is not a requirement but it is'
                    ' listed in "{key}"', exit=False)
                is_valid = False
            elif not Version.is_valid(version_str):
                print_error(
                    f'In {json_path}, "{version_str}" is not a valid version',
                    exit=False)
                is_valid = False

    package_dir = json_path.with_suffix("")
    if not package_dir.is_dir():
        print_error(f"{package_dir} is not a directory", exit=False)
        is_valid = False

    return is_valid


def _extract_houdini_major_minor_from_enable_value(json_path, enable_value):
    # They must provide a strict minimum version, which can be specified in
    # one of the following ways:
    # - "houdini_version >= '20.0'"
    # - {"houdini_version >= '20.0'": true}
    # - {"houdini_version <= '20.0'": false}
    assert enable_value is not None
    enable_dict = ({enable_value: True}
        if isinstance(enable_value, str) else enable_value)

    for condition, enable in enable_dict.items():
        if enable not in (True, False):
            print_warning(f'In {json_path}, "enable" items must be either true'
                ' or false')
            continue

        match = re.match(
            r"^\s*houdini_version\s*(<=|>=)\s*'(.+?)'\s*$", condition)
        if not match:
            continue

        comparison, version = match.groups()
        version_str = version.strip()

        try:
            version = Version(version_str)
        except ValueError:
            is_valid_version = False
        else:
            is_valid_version = len(version.parts) == 2

        if not is_valid_version:
            print_warning(f'In {json_path}, the Houdini version'
                f' {version_str} is not valid.')
            continue

        if (comparison == ">=") == enable:
            return version_str

    return None


def get_status_for_author(package_name):
    authentication = OPTIONS.require_authentication()
    package_name, version, info = _get_package_info_from_name(
        package_name, authentication)

    state = info.get("state")
    if state is None:
        print_error("You are not the author of this package")
    print(f"{package_name}=={version}: {state}")


def grant(package_name, emails):
    authentication = OPTIONS.require_authentication()
    _call_sidefx("hpack.grant_access",
        authentication, package_name, emails)


def publish(package_and_version):
    authentication = OPTIONS.require_authentication()
    package_name, version, _info = _get_package_info_from_name(
        package_and_version, authentication)

    _call_sidefx("hpack.publish_package_version",
        authentication, package_name, version)


def unpublish(package_and_version):
    _unpublish_or_delete(package_and_version, "unpublish")


def delete(package_and_version):
    _unpublish_or_delete(package_and_version, "delete")


def _unpublish_or_delete(package_and_version, operation):
    authentication = OPTIONS.require_authentication()
    package_name, version = _parse_package_and_version(package_and_version)
    if version is None:
        print_error("You must pass <package_name>==<version>")

    _call_sidefx(f"hpack.{operation}_package_version",
        authentication, package_name, version)


# Code related to package json files:
# ----------------------------------------------------------------------------

def _installed_packages():
    result = {}
    for package_dir in _package_path_dirs():
        package_dir = Path(package_dir)
        if not package_dir.is_dir():
            continue

        for json_path in package_dir.glob("*.json"):
            package_name, package_info = _read_package_info_from_json(json_path)
            if package_name:
                assert package_info
                result[package_name] = package_info

    return result


def _read_package_info_from_json(json_path):
    with json_path.open() as open_file:
        try:
            package_json = json.load(open_file)
        except json.JSONDecodeError:
            print_warning(f"{json_path} does not contain valid JSON")
            return None, None

    package_name = package_json.get("name")
    if not package_name:
        return None, None

    version = package_json.get("hpack", {}).get("version")
    if not version:
        return None, None

    # Build a dict mapping from required package name to a version range dict.
    requires_dict = {
        requires_name: {"min_version": "", "max_version": ""}
        for requires_name in package_json.get("requires", [])}
    for list_key, key, operation in (
            ("min_versions", "min_version", "minimum"),
            ("max_versions", "max_version", "maximum")):
        for requires_name, version in package_json["hpack"].get(
                list_key, {}).items():
            if requires_name in requires_dict:
                requires_dict[requires_name][key] = version
            else:
                print_warning(
                    f"'{requires_name}' is not listed as a requirement but has"
                    f" a {operation} version")

    # Now build a list of dicts containing each requirement's name, min
    # version, and max version.
    requires_list = [{
        "name": requires_name,
        "min_version": version_dict["min_version"],
        "max_version": version_dict["max_version"],
    } for requires_name, version_dict in requires_dict.items()]

    # Trim unneeded trailing zeros from the version.
    return package_name, {
        "version": str(Version(version)),
        "location": json_path.with_suffix(""),
        "requires": requires_list,
    }


# Code related to Houdini paths:
# ----------------------------------------------------------------------------

@functools.cache
def _package_path_dirs():
    return [os.path.join(path, "packages")
        for path in _houdini_path_user_dirs()]


@functools.cache
def _houdini_path_user_dirs():
    default_dirs = _default_houdini_path_user_dirs()
    houdini_path = os.environ.get("HOUDINI_PATH")
    if houdini_path:
        houdini_path = houdini_path.split(":")
    else:
        houdini_path = ["@"]

    result = []
    for path in houdini_path:
        if path != "@":
            result.append(path)
        else:
            result.extend(default_dirs)

    # Make sure the result does not contain duplicates.
    return list(dict.fromkeys(result))


@functools.cache
def _default_houdini_path_user_dirs():
    """Return [$HOUDINI_USER_PREF_DIR, $HSITE/houdiniX.Y].
    These are the directories where the user can install packages to.
    """
    result = [_houdini_user_pref_dir()]
    hsite_houdini_dir = _hsite_houdini_dir()
    if hsite_houdini_dir:
        result.append(hsite_houdini_dir)
    return result


@functools.cache
def _hsite_houdini_dir():
    hsite = os.environ.get("HSITE")
    if not hsite:
        return None

    major_minor = _houdini_major_minor()
    hsite_houdini = os.path.join(hsite, f"houdini{major_minor}")
    if not os.path.isdir(hsite_houdini):
        return None
    return hsite_houdini


@functools.cache
def _houdini_user_pref_dir():
    result = os.environ.get("HOUDINI_USER_PREF_DIR")
    if result:
        return result

    major_minor = _houdini_major_minor()
    return os.path.expandvars({
        "Linux": f"$HOME/houdini{major_minor}",
        "Windows": f"%USERPROFILE%/houdini{major_minor}",
        "Darwin": f"$HOME/Library/Preferences/houdini/{major_minor}",
    }[platform.system()])


@functools.cache
def _houdini_major_minor():
    major = os.environ.get("HOUDINI_MAJOR_RELEASE")
    minor = os.environ.get("HOUDINI_MINOR_RELEASE")
    if major and minor:
        return f"{major}.{minor}"

    hfs = _find_hfs()
    if hfs:
        return _read_major_minor_from_hfs(hfs)

    print_error("The current Houdini version could not be determined")
    return None


def _read_major_minor_from_hfs(hfs):
    houdini_setup = Path(hfs) / "houdini_setup_bash"
    if not houdini_setup.is_file():
        return None

    minor, major = None, None
    for line in houdini_setup.read_text().split("\n"):
        match = re.search(r"export HOUDINI_MAJOR_RELEASE=(\d+)", line)
        if match:
            major = match.group(1)
        match = re.search(r"export HOUDINI_MINOR_RELEASE=(\d+)", line)
        if match:
            minor = match.group(1)
        if major and minor:
            return f"{major}.{minor}"

    return None


@functools.cache
def _find_hfs():
    hfs_dirs = []
    hfs = os.environ.get("HFS")
    if hfs:
        hfs_dirs.append(hfs)

    # TODO: Support other platforms.
    if platform.system() == "Linux":
        hfs_dirs.extend(sorted(glob.glob("/opt/hfs*.*.*"), reverse=True))

    for hfs in hfs_dirs:
        path = Path(hfs)
        if path.is_dir() and (path / "houdini_setup_bash").is_file():
            return str(hfs)
    return None


# Code related to authentication and OAuth2 keys for sidefx.com:
# ----------------------------------------------------------------------------

class Authentication:
    def __init__(
            self, session_id=None, csrf_token=None,
            client_id=None, client_secret=None):
        self.session_id = session_id
        self.csrf_token = csrf_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.access_token_expiry_time = None
        self.validation_output = None

        # Only a session id or an OAuth2 client can be given, but not both.
        assert (self.session_id is None) != (self.client_id is None)

        # If a session id is given a csrf token must also be given.
        assert (self.session_id is None) == (self.csrf_token is None)

        # If a client id is given a client secret must also be given.
        assert (self.client_id is None) == (self.client_secret is None)

    def method_name(self):
        if self.session_id and self.client_id:
            return "Session and API Key"
        return ("Session" if self.session_id else "API Key")

    def validate(self):
        if not self.session_id and not self.access_token:
            assert self.client_id
            if not self.redeem_access_token():
                return False

        response = self.validation_output = _post_to_sidefx(
            "/validate/", self, {}, allowed_statuses=(200, 403))
        if response.status_code == 403:
            return False

        output = response.json()
        if output.get("error"):
            print_warning(f"Error calling /validate/: {output.get('error')}")
            return False

        self.validation_output = output
        return True

    def redeem_access_token(self):
        assert self.client_id

        try:
            response = requests.post(
                f"{OPTIONS.server}/oauth2/application_token",
                headers={"Authorization": "Basic " + _b64encode_text(
                    f"{self.client_id}:{self.client_secret}")},
                timeout=OPTIONS.timeout)
        except requests.exceptions.ConnectionError:
            print_error(f"Could not connect to {OPTIONS.server}")
        except requests.exceptions.Timeout:
            print_error(f"Timeout connecting to {OPTIONS.server}")

        if response.status_code == 403:
            return False
        if response.status_code != 200:
            _raise_error_from_web_response(response)

        response_json = response.json()
        self.access_token = response_json["access_token"]
        self.access_token_expiry_time = time.time() - 2 + response_json[
            "expires_in"]
        return True

    def email(self):
        assert self.validation_output
        return self.validation_output["email"]



def _find_authentication(find_all=False):
    authentication_by_session = None
    session_id, csrf_token = _get_session_id_from_hserver()
    if session_id:
        authentication_by_session = Authentication(
            session_id=session_id, csrf_token=csrf_token)
        if not authentication_by_session.validate():
            authentication_by_session = None
            print_warning(
                f"Invalid session id found {session_id}", verbosity=2)

    authentication_by_keys = None
    if not authentication_by_session or find_all:
        for client_id, client_secret in _find_oauth_keys():
            authentication_by_keys = Authentication(
                client_id=client_id, client_secret=client_secret)
            if authentication_by_keys.validate():
                break
            authentication_by_keys = None
            print_warning(
                f"Invalid API key found with client id of {client_id}",
                verbosity=2)

    if authentication_by_keys:
        if authentication_by_session:
            authentication_by_keys.session_id = (
                authentication_by_session.session_id)
        return authentication_by_keys

    if authentication_by_session:
        return authentication_by_session

    return None


def _find_oauth_keys():
    keys = []

    api_key_file = os.environ.get("HOUDINI_API_KEY_FILE")
    if api_key_file:
        api_key_file = Path(api_key_file)
        if api_key_file.is_file():
            keys.extend(_read_api_keys_from_api_key_file(api_key_file))
        else:
            print_warning(
                f"HOUDINI_API_KEY_FILE refers to {str(api_key_file)}"
                " but it does not exist.")

    for path in _find_hserver_ini_paths(os.R_OK):
        keys.extend(_read_api_keys_from_hserver_ini(path))
    return keys


def _find_hserver_ini_paths(mode):
    if platform.system() == "Windows":
        paths = ["%SystemDrive%/ProgramData/SideFX",
            "%USERPROFILE%/AppData/Roaming/SideFX"]
    elif platform.system() == "Darwin":
        paths = ["/Library/Preferences/sesi/hserver",
            "$HOME/Library/Application Support/sidefx"]
    else:
        paths = ["/usr/lib/sesi/hserver",
            "$HOME/.local/share/sidefx"]

    for path in paths:
        path = Path(os.path.expandvars(path)) / "hserver.ini"
        if _can_access_file(path, mode):
            yield path


def _read_api_keys_from_hserver_ini(path):
    # Note that Houdini supports multiple ini file keys, particularly APIKey
    # and APIKeyFile.
    ini = MultiValueConfigParser()
    ini.read(path)

    keys = []
    for section in ini.values():
        client_ids = _get_section_values(section, "ClientID")
        client_secrets = _get_section_values(section, "ClientSecret")
        keys.extend(zip(client_ids, client_secrets))

        for api_key in _get_section_values(section, "APIKey"):
            keys.extend(_read_keys_from_api_key_line(api_key))

        for api_key_file in _get_section_values(section, "APIKeyFile"):
            keys.extend(_read_api_keys_from_api_key_file(api_key_file.strip()))

    return keys


def _get_section_values(section, key):
    """Given a MultiValueConfigParser section, return a key's values."""
    # If there is only one value it won't be a list, so convert it to a list.
    values = section.get(key, [])
    if isinstance(values, str):
        values = [values]
    return values


def _read_api_keys_from_api_key_file(api_key_file):
    keys = []
    if _can_read_file(api_key_file):
        for line in Path(api_key_file).read_text().splitlines():
            keys.extend(_read_keys_from_api_key_line(line))
    return keys


def _read_keys_from_api_key_line(line):
    # line can be one of
    #     <client_id> <client_secret>
    #     <server> <client_id> <client_secret>
    #     <server1> <client_id1> <client_secret1>; <server2> <id2> <secret2>
    keys = []
    for chunk in line.strip().split(";"):
        key_parts = chunk.strip().split()
        if len(key_parts) == 3:
            server, client_id, client_secret = key_parts
            if not server.endswith(".sidefx.com"):
                continue
        elif len(key_parts) == 2:
            client_id, client_secret = key_parts
        else:
            continue
        keys.append((client_id, client_secret))
    return keys


# Code related to ini file parsing:
# ----------------------------------------------------------------------------

class MultiValueConfigParser(configparser.RawConfigParser):
    def __init__(self):
        super().__init__(strict=False, dict_type=MultiValueDict)

    def _join_multiline_values(self):
        # No-op: prevents collapsing lists into "\n".join(...) strings, to
        # support multiple values per name.
        pass

    def _read(self, fp, fpname):
        # Support .ini files that do not have any section headers.
        try:
            return super()._read(fp, fpname)
        except configparser.MissingSectionHeaderError:
            fp.seek(0)
            string_file = io.StringIO("[DEFAULT]\n" + fp.read())
            return super()._read(string_file, fpname)


class MultiValueDict(dict):
    """Accumulate repeated keys into lists of values, for use with the config
    parser.
    """
    def __setitem__(self, key, value):
        if key in self:
            existing = super().__getitem__(key)

            # Both existing and value from _read are lists of strings
            if isinstance(existing, list) and isinstance(value, list):
                existing.extend(value)
                return
            if isinstance(existing, list):
                existing.append(value)
                return
            super().__setitem__(key, [existing] + (
                value if isinstance(value, list) else [value]))
        else:
            super().__setitem__(key, value)


# Code related to calling hserver and sidefx.com:
# ----------------------------------------------------------------------------

def _get_session_id_from_hserver(require_hserver_running=False):
    # Note that hserver only supports pull_cookies in version 20.5.220 and up.
    try:
        session_id_result = _call_hserver("pull_cookies", "sessionid",
            require_hserver_running=require_hserver_running)
    except RuntimeError as e:
        if "unknown api request" not in str(e).lower():
            raise
        print_error("hserver version 20.5.220 or higher is required")

    # If hserver isn't running then the result will be None.
    if session_id_result is None:
        return None, None

    csrf_token_result = _call_hserver("pull_cookies", "csrftoken",
        require_hserver_running=require_hserver_running)

    cookies = (session_id_result.get("cookies", []) +
        csrf_token_result.get("cookies", []))

    session_id, csrf_token = _get_cookie_values(
        cookies, ["sessionid", "csrftoken"])
    if session_id and not csrf_token:
        session_id = None
        print_warning("A session id was found without a CSRF token so it"
            " cannot be used.")
    return session_id, csrf_token


def _get_cookie_values(cookie_strs, cookie_names):
    cookie_domain = _get_cookie_domain()
    num_cookies_left = len(cookie_names)
    cookie_values = [None] * num_cookies_left
    cookie_name_to_index = {cookie_name: i
        for i, cookie_name in enumerate(cookie_names)}

    for cookie_str in cookie_strs:
        cookie_str_parts = cookie_str.split(";")
        if "=" not in cookie_str_parts[0]:
            continue
        cookie_name, cookie_value = cookie_str_parts[0].strip().split("=", 1)
        cookie_index = cookie_name_to_index.get(cookie_name)
        if cookie_index is None:
            continue

        cookie_parts_dict = {}
        for part_name_and_value in cookie_str_parts[1:]:
            if "=" not in part_name_and_value:
                continue
            part_name, value = part_name_and_value.strip().split("=", 1)
            cookie_parts_dict[part_name] = value

        if "domain" not in cookie_parts_dict:
            print_warning("Cookie is missing a domain:\n", cookie_str)
            continue

        if cookie_parts_dict["domain"] == cookie_domain:
            is_overwriting = cookie_values[cookie_index] is not None
            cookie_values[cookie_index] = cookie_value
            if not is_overwriting:
                num_cookies_left -= 1
                if num_cookies_left == 0:
                    break

    return cookie_values


def _get_cookie_domain():
    # Note that cookies don't include the port number in the domain.
    return urllib.parse.urlparse(OPTIONS.server).hostname


def _call_hserver(
        function, *args, method="POST", require_json=True,
        require_hserver_running=True, **kwargs):
    started_hserver = False
    while True:
        try:
            response = requests.request(method, "http://127.0.0.1:1714/api",
                data={"json": json.dumps([function, args, kwargs])},
                headers={"Accept": "application/json"},
                timeout=OPTIONS.timeout)
            break
        except requests.exceptions.ConnectionError:
            if not require_hserver_running:
                print_warning("hserver is not running")
                return None

            if started_hserver:
                print_error("Attempting to start hserver failed")

            if not _start_hserver():
                print_error("hserver is not running and could not be started")
            print("hserver was started")
            started_hserver = True
        except requests.exceptions.Timeout:
            print_error("Timeout connecting to hserver",
                exit=require_hserver_running)
            return None

    if response.status_code == 429:
        print_error("Rate limit exceeded connecting to hserver")
        return None

    if response.status_code != 200:
        raise RuntimeError(response.content.decode())

    try:
        return response.json()
    except json.JSONDecodeError:
        if require_json:
            raise RuntimeError(response.content.decode())
        return response.content.decode()


def _start_hserver():
    hfs = _find_hfs()
    if not hfs:
        return False

    extension = (".exe" if platform.system() == "Windows" else "")
    result = subprocess.run([f"{hfs}/bin/hserver{extension}"], check=False)
    if result.returncode:
        return False

    time.sleep(1)
    return True


def _post_to_sidefx(
        path, authentication, post_data, *, file_data=None,
        allowed_statuses=(200,)):
    assert path.startswith("/")
    assert isinstance(authentication, (Authentication, type(None)))
    if file_data is None:
        file_data = {}
    headers = {"Referer": OPTIONS.server}
    cookies = {}

    if authentication:
        if authentication.session_id:
            post_data = post_data.copy()
            post_data["sessionid"] = authentication.session_id
            post_data["csrftoken"] = authentication.csrf_token
            cookies["sessionid"] = authentication.session_id
            cookies["csrftoken"] = authentication.csrf_token
            headers["X-CSRFToken"] = authentication.csrf_token
        elif authentication.access_token:
            headers["Authorization"] = "Bearer " + authentication.access_token

    try:
        response = requests.post(f"{OPTIONS.server}{path}",
            headers=headers, cookies=cookies, data=post_data, files=file_data,
            timeout=OPTIONS.timeout)
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {OPTIONS.server}")
    except requests.exceptions.Timeout:
        print_error(f"Timeout connecting to {OPTIONS.server}")

    if response.status_code not in allowed_statuses:
        _raise_error_from_web_response(response)
    return response


def _raise_error_from_web_response(response):
    content = response.content.decode()
    if response.status_code != 200:
        if content.strip().startswith("<!DOCTYPE html"):
            content = _extract_text_from_html(content)
        content = f"{response.status_code}\n{content}"
    raise RuntimeError(content)


def _call_sidefx(function, authentication, *args, **kwargs):
    file_data = {}
    for arg_name in list(kwargs):
        arg_value = kwargs[arg_name]
        if isinstance(arg_value, (bytes, bytearray)):
            file_data[arg_name] = (
                "unnamed.bin", io.BytesIO(arg_value),
                "application/octet-stream")
            kwargs.pop(arg_name)

    response = _post_to_sidefx(
        "/api/", authentication, {"json": json.dumps([function, args, kwargs])},
        file_data=file_data, allowed_statuses=(200, 422))
    if response.status_code == 422:
        print_error(response.content.decode())
    if response.headers.get("Content-Type") == "application/octet-stream":
        return response.content
    return response.json()


def _extract_text_from_html(html):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return html

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    chunks = [phrase for line in lines
        for phrase in line.split("  ") if phrase]
    return "\n".join(chunks)


# Code related to version parsing.
# ----------------------------------------------------------------------------

@functools.total_ordering
class Version:
    """Support comparison between N(.N)* version strings like 1, 1.2, 1.2.3."""
    MAX_DIGITS_IN_PARTS = [4, 4, 4, 4, 3]

    def __init__(self, version_str):
        # Note that packaging.version.Version is close to what we want but it's
        # not part of the standard library so we can't easily use it on the
        # Houdini side.
        match = re.match(r"^(\d+(?:\.\d+)*)$", version_str)
        if not match:
            raise ValueError(f"Invalid version: {version_str!r}")

        # Note that we leave trailing ".0"'s.
        parts = []
        for segment in match.group(1).split("."):
            if len(segment) > 1 and segment.startswith("0"):
                raise ValueError(
                    "Version segments cannot have leading zeros:"
                    f" {version_str!r}")
            parts.append(int(segment))

        # Permit versions like 1.0 but trim any later zeros, such as in 1.2.0.
        while len(parts) > 2 and parts[-1] == 0:
            parts.pop()

        if len(parts) > len(self.MAX_DIGITS_IN_PARTS):
            raise ValueError(
                f"Too many segments in version: {version_str!r}")

        for part, max_digits in zip(parts, self.MAX_DIGITS_IN_PARTS):
            if part >= 10 ** max_digits:
                raise ValueError(
                    f"In version: {version_str!r}, the segment {part} is too"
                    " large")

        self.parts = tuple(parts)

    @classmethod
    def is_valid(cls, version_str):
        try:
            Version(version_str)
        except ValueError:
            return False
        return True

    def as_int(self):
        parts = self.parts + (0,) * (
            len(self.MAX_DIGITS_IN_PARTS) - len(self.parts))
        result_strs = []
        for part, max_digits in zip(parts, self.MAX_DIGITS_IN_PARTS):
            result_strs.append(f"{part:0>{max_digits}}")
        return int("".join(result_strs))

    def trimmed_parts(self):
        parts = list(self.parts)
        while len(parts) > 1 and parts[-1] == 0:
            parts.pop()
        return tuple(parts)

    def __eq__(self, other):
        assert isinstance(other, Version)
        return self.trimmed_parts() == other.trimmed_parts()

    def __lt__(self, other):
        assert isinstance(other, Version)
        return self.trimmed_parts() < other.trimmed_parts()

    def __str__(self) -> str:
        return ".".join(str(n) for n in self.parts)

    def __repr__(self) -> str:
        return f"Version({str(self)!r})"


# Miscellaneous helper functions:
# ----------------------------------------------------------------------------

def _download_file(
        authentication, url, path, package_name_and_version, file_size,
        md5_checksum, print_progress=True):
    assert file_size > 0

    # If a partial file exists from an interrupted download, resume from where
    # we left off.
    headers = {"Referer": OPTIONS.server}
    cookies = {}
    if path.exists():
        size_downloaded = path.stat().st_size
        headers["Range"] = f"bytes={size_downloaded}-"
    else:
        size_downloaded = 0

    if authentication:
        if authentication.session_id:
            cookies["sessionid"] = authentication.session_id
        elif authentication.access_token:
            headers["Authorization"] = "Bearer " + authentication.access_token

    # Open a request for the file, retrying if we get rate limited.
    max_retries = 5
    write_mode = "ab"
    session = requests.Session()
    for retries in range(0, max_retries + 1):
        try:
            response = session.get(
                url, headers=headers, cookies=cookies, stream=True,
                timeout=OPTIONS.timeout)
        except requests.exceptions.ConnectionError:
            print_error(f"Could not connect to {OPTIONS.server}")
        except requests.exceptions.Timeout:
            print_error(f"Timeout connecting to {OPTIONS.server}")

        # The server will return http 206 for partial downloads.
        if response.status_code in (200, 206):
            if response.status_code == 200 and size_downloaded > 0:
                write_mode = "wb"
                size_downloaded = 0
            break

        if response.status_code != 429 or retries >= max_retries:
            print_error(f"Error downloading {url}\n"
                f"{response.status_code} {response.text}", word_wrap=False)

        # Handle Retry-After headers with either number of seconds or a
        # specific date.
        retry_after = response.headers.get("Retry-After")
        if retry_after is None:
            retry_after = "30"
        try:
            wait_in_s = int(retry_after)
        except (TypeError, ValueError):
            dt = parsedate_to_datetime(retry_after)
            now = datetime.datetime.now(datetime.timezone.utc)
            wait_in_s = (dt - now).total_seconds()

        wait_in_s = max(wait_in_s, 1)
        wait_in_s = min(wait_in_s, 120)
        if print_progress:
            _print_progress_bar(
                0.0, suffix=f"(rate limited) {package_name_and_version}")
        time.sleep(wait_in_s)
        continue

    # Download the file in chunks, updating the progress bar.
    with path.open(write_mode) as open_file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if not chunk:
                continue
            open_file.write(chunk)
            size_downloaded += len(chunk)
            if print_progress:
                _print_progress_bar(
                    size_downloaded / file_size,
                    suffix=package_name_and_version)
    message = f"\rSuccessfully installed {package_name_and_version}"
    print(f"{message:<{_num_terminal_cols()}}")

    # Verify that we got the right final file size and checksum.
    actual_file_size = path.stat().st_size
    actual_md5_checksum = _md5_checksum_file(path)
    if actual_file_size != file_size or actual_md5_checksum != md5_checksum:
        path.unlink()
        print_error(
            "The data that was downloaded does not match what was expected.\n"
            f"File size: expected {file_size}, got {actual_file_size}\n"
            f"Checksum: expected {md5_checksum}, got {actual_md5_checksum}")


def _print_progress_bar(fraction, prefix="", suffix=""):
    bar_width = max(
        10, _num_terminal_cols() - len(prefix) - max(len(suffix), 60))
    percent = f"{(100 * fraction):1.1f}"
    filled = int(bar_width * fraction)
    bar_str = "#" * filled + "-" * (bar_width - filled)
    sys.stdout.write(f"\r{prefix} [{bar_str}] {percent:>5}% {suffix[:49]}")
    sys.stdout.flush()


def _prompt(message, default_to_y):
    yes_no = ("([y]/n)" if default_to_y else "(y/[n])")
    while True:
        try:
            answer = input(f"{message} {yes_no} ")
        except EOFError:
            print_error("\nStandard input is not available, aborting."
                " Consider passing --yes.")

        if not answer:
            return default_to_y
        if answer.lower() in ("y", "yes"):
            return True
        if answer.lower() in ("n", "no"):
            return False


def _extract_zip(zip_path, to_dir):
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(to_dir)


def _md5_checksum_file(file_path):
    hasher = hashlib.md5()
    with open(file_path, "rb") as open_file:
        for chunk in iter(lambda: open_file.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _num_terminal_cols():
    return shutil.get_terminal_size(fallback=(80, 20)).columns


def print_error(message, exit=True, word_wrap=True):
    _print_message(message, "Error: ", exit, word_wrap)


def print_warning(message, verbosity=1, word_wrap=True):
    if OPTIONS.verbosity < verbosity:
        return
    _print_message(message, "Warning: ", exit=False, word_wrap=word_wrap)


def _print_message(message, message_prefix, exit, word_wrap):
    message = message_prefix + message
    if word_wrap:
        message = "\n".join(
            textwrap.fill(
                line, _num_terminal_cols(), break_long_words=False,
                replace_whitespace=False)
            for line in message.splitlines())
    if not message.endswith("\n"):
        message += "\n"
    sys.stderr.write(message)
    if exit:
        sys.exit(1)


def _can_access_file(file_path, mode):
    assert mode in (os.R_OK, os.W_OK)
    path = Path(file_path)
    if path.exists():
        return path.is_file() and os.access(path, mode)

    return (mode == os.W_OK and path.parent.is_dir() and
        os.access(path.parent, os.W_OK))


def _can_read_file(file_path):
    return _can_access_file(file_path, os.R_OK)


def _b64encode_text(text):
    return base64.b64encode(text.encode()).decode()


if __name__ == "__main__":
    main()
