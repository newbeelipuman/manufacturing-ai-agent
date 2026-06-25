from __future__ import annotations

from pathlib import Path

from scripts import run_ci_checks


def test_pytest_env_uses_workspace_temp_dir() -> None:
    env = run_ci_checks.pytest_env()

    assert env["TMP"] == str(run_ci_checks.PYTEST_TEMP_DIR)
    assert env["TEMP"] == str(run_ci_checks.PYTEST_TEMP_DIR)
    assert run_ci_checks.PYTEST_TEMP_DIR.exists()


def test_run_ci_checks_passes_pytest_basetemp(monkeypatch) -> None:
    calls: list[tuple[list[str], Path, dict[str, str] | None]] = []

    def fake_run(
        command: list[str],
        cwd: Path = run_ci_checks.ROOT_DIR,
        env: dict[str, str] | None = None,
    ) -> None:
        calls.append((command, cwd, env))

    monkeypatch.setattr(run_ci_checks, "run", fake_run)
    monkeypatch.delenv("VERIFY_DEPLOYMENT_BASE_URL", raising=False)

    run_ci_checks.main()

    pytest_calls = [
        call for call in calls if call[0][:3] == [run_ci_checks.sys.executable, "-m", "pytest"]
    ]
    assert len(pytest_calls) == 1
    pytest_command, _, pytest_env = pytest_calls[0]
    assert "--basetemp" in pytest_command
    assert "-p" in pytest_command
    assert "no:cacheprovider" in pytest_command
    assert str(run_ci_checks.PYTEST_TEMP_DIR) in pytest_command
    assert pytest_env is not None
    assert pytest_env["TMP"] == str(run_ci_checks.PYTEST_TEMP_DIR)


def test_docker_env_uses_workspace_config_dir() -> None:
    env = run_ci_checks.docker_env()

    assert env["DOCKER_CONFIG"] == str(run_ci_checks.DOCKER_CONFIG_DIR)
    assert run_ci_checks.DOCKER_CONFIG_DIR.exists()


def test_run_ci_checks_passes_docker_config_env(monkeypatch) -> None:
    calls: list[tuple[list[str], Path, dict[str, str] | None]] = []

    def fake_run(
        command: list[str],
        cwd: Path = run_ci_checks.ROOT_DIR,
        env: dict[str, str] | None = None,
    ) -> None:
        calls.append((command, cwd, env))

    monkeypatch.setattr(run_ci_checks, "run", fake_run)
    monkeypatch.delenv("VERIFY_DEPLOYMENT_BASE_URL", raising=False)

    run_ci_checks.main()

    docker_calls = [call for call in calls if call[0] == ["docker", "compose", "config"]]
    assert len(docker_calls) == 1
    _, _, docker_env = docker_calls[0]
    assert docker_env is not None
    assert docker_env["DOCKER_CONFIG"] == str(run_ci_checks.DOCKER_CONFIG_DIR)


def test_run_ci_checks_marks_loopback_deployment_verification_as_local(
    monkeypatch,
) -> None:
    calls: list[tuple[list[str], Path, dict[str, str] | None]] = []

    def fake_run(
        command: list[str],
        cwd: Path = run_ci_checks.ROOT_DIR,
        env: dict[str, str] | None = None,
    ) -> None:
        calls.append((command, cwd, env))

    monkeypatch.setattr(run_ci_checks, "run", fake_run)
    monkeypatch.setenv("VERIFY_DEPLOYMENT_BASE_URL", "http://localhost:8080")

    run_ci_checks.main()

    verify_calls = [
        call
        for call in calls
        if call[0][:2] == [run_ci_checks.sys.executable, "scripts/verify_cloud_deployment.py"]
    ]
    assert len(verify_calls) == 1
    assert verify_calls[0][0][-2:] == ["--environment", "local"]


def test_run_ci_checks_marks_non_loopback_deployment_verification_as_cloud(
    monkeypatch,
) -> None:
    calls: list[tuple[list[str], Path, dict[str, str] | None]] = []

    def fake_run(
        command: list[str],
        cwd: Path = run_ci_checks.ROOT_DIR,
        env: dict[str, str] | None = None,
    ) -> None:
        calls.append((command, cwd, env))

    monkeypatch.setattr(run_ci_checks, "run", fake_run)
    monkeypatch.setenv("VERIFY_DEPLOYMENT_BASE_URL", "http://203.0.113.10")

    run_ci_checks.main()

    verify_calls = [
        call
        for call in calls
        if call[0][:2] == [run_ci_checks.sys.executable, "scripts/verify_cloud_deployment.py"]
    ]
    assert len(verify_calls) == 1
    assert verify_calls[0][0][-2:] == ["--environment", "cloud"]
