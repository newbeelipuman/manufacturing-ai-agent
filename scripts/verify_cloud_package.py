from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.package_cloud_deployment import ROOT_DIR, verify_package_metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify cloud deployment zip checksum, manifest, and exclusions."
    )
    parser.add_argument(
        "--package",
        default="dist-cloud/manufacturing-ai-agent-cloud.zip",
        help="Path to the cloud deployment zip.",
    )
    args = parser.parse_args()

    package_path = (ROOT_DIR / args.package).resolve()
    errors = verify_package_metadata(package_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print(f"Cloud deployment package verified: {package_path}")


if __name__ == "__main__":
    main()
