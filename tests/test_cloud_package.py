from pathlib import Path
from zipfile import ZipFile
import json

from scripts.package_cloud_deployment import (
    create_package,
    file_sha256,
    should_include,
    validate_required_files,
    verify_package_metadata,
    write_package_metadata,
)


def test_cloud_package_required_files_exist() -> None:
    assert validate_required_files() == []


def test_cloud_package_excludes_env_database_and_node_modules() -> None:
    root = Path.cwd()

    assert not should_include(root / ".env")
    assert not should_include(root / "local_dev.db")
    assert not should_include(root / "frontend" / "node_modules" / "x.js")
    assert not should_include(root / "app" / "__pycache__" / "x.pyc")
    assert not should_include(root / "dist-cloud" / "old.zip")
    assert not should_include(root / ".docker-config-tmp" / "config.json")
    assert not should_include(root / ".pytest-tmp" / "test.log")


def test_cloud_package_includes_runtime_sources_and_frontend_dist() -> None:
    root = Path.cwd()

    assert should_include(root / "app" / "main.py")
    assert should_include(root / "docker-compose.yml")
    assert should_include(root / "frontend" / "dist" / "index.html")


def test_cloud_package_zip_excludes_local_secrets_and_runtime_noise(tmp_path: Path) -> None:
    output = tmp_path / "cloud.zip"

    count = create_package(output)

    assert count > 0
    with ZipFile(output) as archive:
        names = set(archive.namelist())

    assert "app/main.py" in names
    assert "docker-compose.yml" in names
    assert "frontend/dist/index.html" in names
    assert ".env" not in names
    assert ".env.production" not in names
    assert "local_dev.db" not in names
    assert not any("node_modules/" in name for name in names)
    assert not any("__pycache__/" in name for name in names)
    assert not any(name.startswith(".docker-config-tmp/") for name in names)
    assert not any(name.startswith(".pytest-tmp/") for name in names)


def test_cloud_package_metadata_records_checksum_and_boundary(tmp_path: Path) -> None:
    output = tmp_path / "cloud.zip"

    count = create_package(output)
    manifest_path, checksum_path = write_package_metadata(output, count)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksum_text = checksum_path.read_text(encoding="utf-8")

    assert manifest["sha256"] == file_sha256(output)
    assert manifest["file_count"] == count
    assert manifest["cloud_status"] == "prepared_only_not_cloud_verified"
    assert "模拟 ERP/MES/WMS 数据" in "\n".join(manifest["boundary"])
    assert checksum_text == f"{manifest['sha256']}  {output.name}\n"
    assert manifest["server_verify_command"] == f"sha256sum -c {checksum_path.name}"
    assert verify_package_metadata(output) == []


def test_cloud_package_metadata_verifier_detects_tampering(tmp_path: Path) -> None:
    output = tmp_path / "cloud.zip"

    count = create_package(output)
    write_package_metadata(output, count)
    with output.open("ab") as handle:
        handle.write(b"tamper")

    errors = verify_package_metadata(output)

    assert any("sha256" in error for error in errors)
    assert any("Checksum file" in error for error in errors)
