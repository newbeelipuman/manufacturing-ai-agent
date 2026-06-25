from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".docker-config-tmp",
    ".pytest_cache",
    ".pytest-tmp",
    ".pytest-workspace-tmp",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist-cloud",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".db",
    ".sqlite",
    ".sqlite3",
}

EXCLUDED_FILENAMES = {
    ".env",
    ".env.production",
    "local_dev.db",
    "test_m2.db",
}

REQUIRED_FILES = [
    "app/main.py",
    "docker-compose.yml",
    "docker-compose.cloud.yml",
    "docker/Dockerfile",
    "docker/nginx.Dockerfile",
    "docker/nginx.conf",
    "frontend/dist/index.html",
    "requirements.txt",
    ".env.production.example",
]

BOUNDARY_TEXT = [
    "本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。",
    "Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。",
    "后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。",
]


def should_include(path: Path, root_dir: Path = ROOT_DIR) -> bool:
    relative = path.relative_to(root_dir)
    parts = set(relative.parts)
    if parts & EXCLUDED_DIRS:
        return False
    if path.name in EXCLUDED_FILENAMES:
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def validate_required_files(root_dir: Path = ROOT_DIR) -> list[str]:
    missing: list[str] = []
    for item in REQUIRED_FILES:
        if not (root_dir / item).exists():
            missing.append(item)
    return missing


def create_package(output: Path, root_dir: Path = ROOT_DIR) -> int:
    missing = validate_required_files(root_dir)
    if missing:
        raise SystemExit(
            "Missing required files. Run frontend build first if dist is missing: "
            + ", ".join(missing)
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    file_count = 0
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in sorted(root_dir.rglob("*")):
            if not path.is_file() or path == output:
                continue
            if not should_include(path, root_dir):
                continue
            archive.write(path, path.relative_to(root_dir).as_posix())
            file_count += 1
    return file_count


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_package_metadata(
    output: Path, file_count: int, root_dir: Path = ROOT_DIR
) -> tuple[Path, Path]:
    sha256 = file_sha256(output)
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    relative_output = output.relative_to(root_dir) if output.is_relative_to(root_dir) else output
    manifest = {
        "package": str(relative_output).replace("\\", "/"),
        "sha256": sha256,
        "file_count": file_count,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "boundary": BOUNDARY_TEXT,
        "excluded": {
            "directories": sorted(EXCLUDED_DIRS),
            "filenames": sorted(EXCLUDED_FILENAMES),
            "suffixes": sorted(EXCLUDED_SUFFIXES),
        },
        "server_verify_command": f"sha256sum -c {checksum_path.name}",
        "cloud_status": "prepared_only_not_cloud_verified",
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    checksum_path.write_text(f"{sha256}  {output.name}\n", encoding="utf-8")
    return manifest_path, checksum_path


def verify_package_metadata(output: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    if not output.exists():
        return [f"Package not found: {output}"]
    if not manifest_path.exists():
        errors.append(f"Manifest not found: {manifest_path}")
    if not checksum_path.exists():
        errors.append(f"Checksum not found: {checksum_path}")
    if errors:
        return errors

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Manifest is not valid JSON: {exc}"]

    actual_sha256 = file_sha256(output)
    expected_sha256 = manifest.get("sha256")
    if expected_sha256 != actual_sha256:
        errors.append("Manifest sha256 does not match package.")

    checksum_text = checksum_path.read_text(encoding="utf-8").strip()
    if checksum_text != f"{actual_sha256}  {output.name}":
        errors.append("Checksum file does not match package.")

    if manifest.get("cloud_status") != "prepared_only_not_cloud_verified":
        errors.append("Manifest cloud_status must remain prepared_only_not_cloud_verified.")

    if manifest.get("file_count", 0) <= 0:
        errors.append("Manifest file_count must be positive.")

    boundary = "\n".join(manifest.get("boundary", []))
    for required_text in BOUNDARY_TEXT[:2]:
        if required_text not in boundary:
            errors.append("Manifest boundary text is incomplete.")
            break

    with ZipFile(output) as archive:
        names = set(archive.namelist())
    forbidden_names = {".env", ".env.production", "local_dev.db", "test_m2.db"}
    present_forbidden = sorted(forbidden_names & names)
    if present_forbidden:
        errors.append("Package includes forbidden files: " + ", ".join(present_forbidden))
    if any(name.startswith("dist-cloud/") for name in names):
        errors.append("Package must not include dist-cloud artifacts.")
    if any(name.startswith(".pytest-workspace-tmp/") for name in names):
        errors.append("Package must not include workspace pytest temp artifacts.")
    if any("node_modules/" in name for name in names):
        errors.append("Package must not include node_modules.")
    if any("__pycache__/" in name for name in names):
        errors.append("Package must not include Python cache directories.")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a clean deployment zip for cloud-server upload."
    )
    parser.add_argument(
        "--output",
        default="dist-cloud/manufacturing-ai-agent-cloud.zip",
        help="Output zip path.",
    )
    args = parser.parse_args()

    output = (ROOT_DIR / args.output).resolve()
    count = create_package(output)
    manifest_path, checksum_path = write_package_metadata(output, count)
    print(f"Cloud deployment package written: {output}")
    print(f"Packaged files: {count}")
    print(f"Package manifest written: {manifest_path}")
    print(f"Package checksum written: {checksum_path}")


if __name__ == "__main__":
    main()
