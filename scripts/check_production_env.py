from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_UNSAFE_VALUES = {
    "POSTGRES_PASSWORD": {"agent_password", "change_me_before_deploy", ""},
    "AUTH_SECRET_KEY": {
        "dev-only-change-me",
        "change_me_to_a_long_random_secret",
        "",
    },
}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lstrip("\ufeff")] = value.strip().strip('"').strip("'")
    return values


def validate_env(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if values.get("ENVIRONMENT") != "production":
        errors.append("ENVIRONMENT must be production.")

    for key, unsafe_values in DEFAULT_UNSAFE_VALUES.items():
        value = values.get(key, "")
        if value in unsafe_values:
            errors.append(f"{key} must be changed from the default demo value.")

    database_url = values.get("DATABASE_URL", "")
    postgres_password = values.get("POSTGRES_PASSWORD", "")
    if not database_url.startswith("postgresql+psycopg://"):
        errors.append("DATABASE_URL must use postgresql+psycopg:// for cloud deployment.")
    if postgres_password and postgres_password not in database_url:
        errors.append("DATABASE_URL should include the configured POSTGRES_PASSWORD.")
    if "sqlite" in database_url.lower():
        errors.append("DATABASE_URL must not use SQLite in production.")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate .env.production before cloud deployment."
    )
    parser.add_argument(
        "--env-file",
        default=".env.production",
        help="Path to the production env file. Default: .env.production",
    )
    args = parser.parse_args()

    path = Path(args.env_file)
    if not path.exists():
        raise SystemExit(f"Env file not found: {path}")

    errors = validate_env(load_env(path))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"Production env check passed: {path}")


if __name__ == "__main__":
    main()
