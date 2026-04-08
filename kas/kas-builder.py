#!/usr/bin/env -S uv run --script
#
# /// script
# dependencies = [
#   "docker",
#   "pyyaml",
#   "questionary",
#   "rich",
#   "tomli_w",
# ]
# ///

import argparse
import datetime
import logging
import os
import pathlib
import re
import shlex
import subprocess
import sys
import threading
import time
import tomllib
from enum import IntEnum

import docker
import tomli_w
import questionary
import yaml
from rich.console import Console

logger = logging.getLogger("image-builder")

CONSOLE = Console()
CUSTOM_STYLE = questionary.Style(
    [
        ("answer", "noinherit bold italic fg:#FF9D00"),
        ("pointer", "noinherit bold italic fg:#FF9D00"),
        ("selected", "noinherit bold italic fg:#FF9D00"),
    ]
)
DISTROS = [
    "helios9-distro",
]
LAYER = {
    "name": "meta-helios9",
    "url": "https://github.com/thokis/meta-helios9.git",
}
MACHINES = {
    "raspberrypi3": {
        "include": ["include/raspberrypi.yaml"],
    },
    "raspberrypi3-64": {
        "include": ["include/raspberrypi.yaml"],
    },
    "qemuarm": {
        "include": ["include/qemuarm.yaml"],
    },
    "qemuarm-64": {
        "include": ["include/qemuarm.yaml"],
    },
}
PATH = pathlib.Path(f"{os.environ['HOME']}/.local/share/kas-builder/")
PATH.mkdir(parents=True, exist_ok=True)
REPOS = dict()
TARGETS = [
    "helios9-image-minimal",
    "helios9-image-wwan",
]


class Device(IntEnum):
    """Device enumeration."""

    SD = 0
    EMMC = 2


def __yaml_dict_representer__(dumper, data):
    if not data:
        return dumper.represent_scalar("tag:yaml.org,2002:", "")
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


def __yaml_str_representer__(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def get_all_branches(name: str, url: str):
    command = f"git ls-remote -h {url}"
    with CONSOLE.status(
        f"[bold italic]fetching branches from [#FF9D00]{name}",
        spinner="bouncingBar",
        spinner_style="#FF9D00",
    ):
        result = subprocess.run(
            shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
    if result.returncode != 0:
        logger.error(
            "git ls-remote failed for %s (%s): %s", name, url, result.stdout.decode()
        )
        raise RuntimeError(f"failed to fetch branches from {name} ({url})")
    branches = [line for line in result.stdout.decode().splitlines()]
    branches = ["/".join(branch.split("/")[2:]) for branch in branches]
    return list(filter(None, branches))


def get_default_branch(name: str, url: str):
    command = f"git ls-remote --symref {url} HEAD"
    with CONSOLE.status(
        f"[bold italic]fetching default branch for [#FF9D00]{name}",
        spinner="bouncingBar",
        spinner_style="#FF9D00",
    ):
        result = subprocess.run(
            shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
    if result.returncode != 0:
        logger.error(
            "git ls-remote failed for %s (%s): %s", name, url, result.stdout.decode()
        )
        raise RuntimeError(f"failed to fetch default branch from {name} ({url})")
    match = re.search(r"ref: refs/heads/(.*)HEAD", result.stdout.decode())
    return match.group(1).rstrip() if match else None


def get_distro():
    distro = questionary.select(
        "select distro:",
        choices=DISTROS,
    ).ask()
    if distro is not None:
        return distro
    raise KeyboardInterrupt()


def get_kas_config():
    config = dict()
    config["distro"] = get_distro()
    config["header"] = dict()
    config["header"]["version"] = 18
    config["header"]["includes"] = ["include/common.yaml", "include/helios9.yaml"]

    machine = get_machine()
    config["machine"] = machine
    if MACHINES[machine].get("include"):
        config["header"]["includes"] += MACHINES[machine]["include"]

    config["repos"] = dict()

    name = LAYER["name"]
    url = LAYER["url"]
    if questionary.confirm(f"select {name} branch", default=False).ask():
        branch = select_branch(name, url)
    else:
        branch = get_default_branch(name, url)

    config["repos"][name] = dict()
    config["repos"][name]["url"] = url
    config["repos"][name]["branch"] = branch
    config["repos"][name]["commit"] = get_latest_commit_from_branch(branch, url)

    config["target"] = get_target()

    if len(REPOS):
        branches_variable = list()
        selected_repos = get_selected_repos()

        for repo in REPOS.keys():
            name = repo["name"]
            url = repo["url"]
            variable = repo["variable"]
            if repo in selected_repos:
                branch = select_branch(name, url)
            else:
                branch = get_default_branch(name, url)
            branches_variable.append(f'{variable} = "{branch}"')

        config["local_conf_header"] = dict()
        config["local_conf_header"]["branches"] = "\n".join(branches_variable)

    return config


def get_kas_path() -> pathlib.Path:
    kas_path = questionary.path(
        "path to kas repository",
        style=CUSTOM_STYLE,
    ).ask()

    if kas_path:
        return pathlib.Path(kas_path)
    raise KeyboardInterrupt()


def get_latest_commit_from_branch(branch: str, url: str):
    command = f"git ls-remote {url} refs/heads/{branch}"
    command += " | awk '{print $1}'"
    with CONSOLE.status(
        f"[bold italic]fetching latest commit from [#FF9D00]{branch}",
        spinner="bouncingBar",
        spinner_style="#FF9D00",
    ):
        result = subprocess.run(
            shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
    if result.returncode != 0:
        logger.error(
            "git ls-remote failed for %s (%s): %s", branch, url, result.stdout.decode()
        )
        raise RuntimeError(f"failed to fetch latest commit from {branch} ({url})")
    result.stdout.decode()


def get_machine():
    machine = questionary.select(
        "select machine:",
        choices=MACHINES.keys(),
    ).ask()
    if machine is not None:
        return machine
    raise KeyboardInterrupt()


def get_selected_repos():
    selected_repos = questionary.checkbox(
        "select repos:",
        choices=[questionary.Choice(x, checked=True) for x in REPOS.keys()],
        style=CUSTOM_STYLE,
    ).ask()

    if selected_repos is not None:
        return selected_repos
    raise KeyboardInterrupt()


def get_target():
    target = questionary.select(
        "select target:",
        choices=TARGETS,
    ).ask()
    if target is not None:
        return target
    raise KeyboardInterrupt()


def select_branch(name: str, url: str):
    branches = get_all_branches(name, url)
    default_branch = get_default_branch(name, url)
    selection = questionary.autocomplete(
        f"select {name} branch:",
        style=CUSTOM_STYLE,
        default=default_branch,
        choices=branches,
        validate=lambda text: (
            True if text in branches else "Please select a valid branch"
        ),
    ).ask()
    if selection is not None:
        return selection
    raise KeyboardInterrupt()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--print", action="store_true", help="print stored settings")
    parser.add_argument("--clear", action="store_true", help="clear stored settings")
    parser.add_argument("-v", action="store_true", help="info level logging")
    parser.add_argument("-vv", action="store_true", help="debug level logging")
    parser.add_argument("-vvv", action="store_true", help="trace level logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG
        if args.vvv or args.vv
        else logging.INFO
        if args.v
        else logging.WARNING,
        format="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    )

    yaml.add_representer(str, __yaml_str_representer__)
    yaml.add_representer(dict, __yaml_dict_representer__)

    PATH.mkdir(parents=True, exist_ok=True)

    if args.print:
        try:
            with (PATH / "kas.yaml").open() as f:
                kas_config = yaml.safe_load(f)
            print(yaml.safe_dump(kas_config, indent=4))
            sys.exit(0)
        except FileNotFoundError:
            sys.exit(1)

    if args.clear:
        (PATH / "kas.yaml").unlink(missing_ok=True)

    try:
        with (PATH / "kas.yaml").open() as f:
            kas_config = yaml.safe_load(f)
            questionary.print("stored kas configuration:\n", style="bold", end="")
            questionary.print(
                yaml.dump(kas_config, indent=4), style="italic fg:#FF9D00"
            )
        reuse = questionary.confirm("build image using stored configuration").ask()
        if reuse is None:
            raise KeyboardInterrupt()
        if not reuse:
            kas_config = kas_config | get_kas_config()
    except FileNotFoundError:
        kas_config = get_kas_config()

    try:
        with (PATH / "settings.toml").open("rb") as f:
            kas_builder_settings = tomllib.load(f)

        if (
            "kas" not in kas_builder_settings
            or kas_builder_settings["kas"].get("path") is None
        ):
            raise FileNotFoundError()
        else:
            kas_path = pathlib.Path(kas_builder_settings["kas"]["path"])
    except FileNotFoundError:
        kas_path = get_kas_path()
        kas_builder_settings = dict()
        kas_builder_settings["kas"] = dict()
        kas_builder_settings["kas"]["path"] = str(kas_path)

    with (PATH / "settings.toml").open("wb") as f:
        tomli_w.dump(kas_builder_settings, f)

    (PATH / "kas.yaml").write_text(
        yaml.dump(kas_config, indent=4, default_flow_style=False)
    )

    command = "kas build custom.yaml"
    logger.info("executing command '%s'", command)

    client = docker.from_env()

    user = f"{os.getuid()}:{os.getgid()}"

    ssh_known_hosts = (
        pathlib.Path(os.environ.get("SSH_FOLDER", os.path.expanduser("~/.ssh")))
        / "known_hosts"
    )
    ssh_auth_sock = os.environ.get("SSH_AUTH_SOCK")

    container = None
    try:
        with CONSOLE.status(
            f"[bold italic]building [#FF9D00]{kas_config['target']}",
            spinner="bouncingBar",
            spinner_style="#FF9D00",
        ):
            container = client.containers.run(
                name="kas",
                image="yocto.kas",
                command=["/bin/bash", "-c", command],
                environment={"SSH_AUTH_SOCK": "/ssh-agent"},
                volumes=[
                    f"{str(ssh_known_hosts)}:/home/kas/.ssh/known_hosts:ro",
                    f"{ssh_auth_sock}:/ssh-agent:ro",
                    f"{str(kas_path)}/yocto:/home/kas/yocto:z",
                    f"{str(PATH / 'kas.yaml')}:/home/kas/yocto/.config.yaml:ro",
                ],
                user=user,
                detach=True,
                stop_signal="SIGINT",
                working_dir="/home/kas/yocto",
            )

            status = container.wait()

        logs = container.logs(stdout=True, stderr=True).decode("utf-8")
        now = datetime.datetime.now()
        logfile = PATH / f"logs/build_{now.strftime('%Y-%m-%d_%H:%M:%S')}.log"
        logfile.parent.mkdir(parents=True, exist_ok=True)
        with logfile.open("w") as f:
            f.write(logs)

        if status["StatusCode"] != 0:
            print(container.logs().decode("utf-8"))
            sys.exit(status["StatusCode"])
    finally:
        if container is not None:
            container.stop()
            container.remove()

    if kas_config["machine"] == "qemuarm":
        sock_path = "/tmp/qemu-console.sock"
        pty_link = "/tmp/vserial0"

        # Clean up stale files
        for p in (sock_path, pty_link):
            try:
                os.remove(p)
            except FileNotFoundError:
                pass

        socat_proc = None

        def serial_bridge():
            nonlocal socat_proc
            while not os.path.exists(sock_path):
                time.sleep(0.1)
            socat_proc = subprocess.Popen(
                [
                    "socat",
                    f"pty,link={pty_link},raw,echo=0",
                    f"unix-connect:{sock_path}",
                ],
            )
            questionary.print("serial console available at: ", style="bold", end="")
            questionary.print(pty_link, style="italic fg:#FF9D00")

        bridge_thread = threading.Thread(target=serial_bridge, daemon=True)
        bridge_thread.start()

        try:
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-it",
                    "--rm",
                    "--privileged",
                    "-e",
                    "SSH_AUTH_SOCK=/ssh-agent",
                    "-v",
                    "/dev/bus/usb:/dev/bus/usb",
                    "-v",
                    f"{str(ssh_known_hosts)}:/home/kas/.ssh/known_hosts:ro",
                    "-v",
                    f"{ssh_auth_sock}:/ssh-agent:ro",
                    "-v",
                    f"{str(kas_path)}/yocto:/home/kas/yocto:z",
                    "-v",
                    f"{str(PATH / 'kas.yaml')}:/home/kas/yocto/.config.yaml:ro",
                    "-v",
                    "/tmp:/tmp",
                    "-w",
                    "/home/kas/yocto",
                    "yocto.kas",
                    "uv",
                    "run",
                    "kas",
                    "shell",
                    "qemuarm.yaml",
                    "-c",
                    'runqemu nographic slirp qemuparams="-serial unix:{sock_path},server,nowait -device usb-host,vendorid=0x2c7c,productid=0x6002,bus=usb-bus.0,id=modem"',
                ],
            )
        finally:
            if socat_proc:
                socat_proc.terminate()
                socat_proc.wait()
            for p in (sock_path, pty_link):
                try:
                    os.remove(p)
                except FileNotFoundError:
                    pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
