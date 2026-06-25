from __future__ import annotations

import subprocess
import sys
import os
import ipaddress
from shutil import which
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parents[1]
PYTEST_TEMP_ROOT = ROOT_DIR / ".pytest-workspace-tmp"
PYTEST_TEMP_DIR = PYTEST_TEMP_ROOT / f"run-{os.getpid()}"
DOCKER_CONFIG_DIR = ROOT_DIR / ".docker-config-tmp"


def is_loopback_base_url(base_url: str) -> bool:
    host = urlparse(base_url).hostname
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def run(command: list[str], cwd: Path = ROOT_DIR, env: dict[str, str] | None = None) -> None:
    executable = which(command[0])
    if executable:
        command = [executable, *command[1:]]
    print(f"\n$ {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def pytest_env() -> dict[str, str]:
    PYTEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TMP"] = str(PYTEST_TEMP_DIR)
    env["TEMP"] = str(PYTEST_TEMP_DIR)
    return env


def docker_env() -> dict[str, str]:
    DOCKER_CONFIG_DIR.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["DOCKER_CONFIG"] = str(DOCKER_CONFIG_DIR)
    return env


def main() -> None:
    run([sys.executable, "-m", "compileall", "app"])
    run([sys.executable, "-m", "compileall", "scripts"])
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--basetemp",
            str(PYTEST_TEMP_DIR),
            "-p",
            "no:cacheprovider",
        ],
        env=pytest_env(),
    )
    run(["npm", "run", "test:smoke"], cwd=ROOT_DIR / "frontend")
    run(["npm", "run", "build"], cwd=ROOT_DIR / "frontend")
    run([sys.executable, "scripts/package_cloud_deployment.py"])
    run([sys.executable, "scripts/verify_cloud_package.py"])
    run([sys.executable, "scripts/verify_cloud_report.py"])
    run(["docker", "compose", "config"], env=docker_env())
    run([sys.executable, "scripts/run_demo_report.py"])
    run([sys.executable, "scripts/run_rag_eval.py"])
    verify_base_url = os.getenv("VERIFY_DEPLOYMENT_BASE_URL")
    if verify_base_url:
        environment = "local" if is_loopback_base_url(verify_base_url) else "cloud"
        run(
            [
                sys.executable,
                "scripts/verify_cloud_deployment.py",
                "--base-url",
                verify_base_url,
                "--environment",
                environment,
            ]
        )


if __name__ == "__main__":
    main()
