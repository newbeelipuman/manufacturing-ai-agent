from pathlib import Path

from scripts.check_production_env import load_env, validate_env


def test_production_env_example_rejected_until_secrets_are_changed() -> None:
    values = load_env(Path(".env.production.example"))
    errors = validate_env(values)

    assert any("POSTGRES_PASSWORD" in error for error in errors)
    assert any("AUTH_SECRET_KEY" in error for error in errors)


def test_production_env_accepts_changed_postgres_and_secret() -> None:
    values = {
        "ENVIRONMENT": "production",
        "POSTGRES_PASSWORD": "strong_demo_password_123",
        "AUTH_SECRET_KEY": "long_random_secret_for_cloud_demo_123456",
        "DATABASE_URL": (
            "postgresql+psycopg://agent_user:strong_demo_password_123"
            "@postgres:5432/manufacturing_ai_agent"
        ),
    }

    assert validate_env(values) == []


def test_production_env_rejects_sqlite() -> None:
    values = {
        "ENVIRONMENT": "production",
        "POSTGRES_PASSWORD": "strong_demo_password_123",
        "AUTH_SECRET_KEY": "long_random_secret_for_cloud_demo_123456",
        "DATABASE_URL": "sqlite:///./local_dev.db",
    }

    assert any("SQLite" in error for error in validate_env(values))
