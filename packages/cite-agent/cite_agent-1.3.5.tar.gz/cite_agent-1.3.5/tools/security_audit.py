#!/usr/bin/env python3
"""Lightweight security audit for environment variables.

Run this script inside the deployment environment to verify that all
critical secrets are configured and that no placeholder values remain.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class SecretCheck:
    name: str
    placeholder_values: Iterable[str]
    help: str
    optional: bool = False


REQUIRED_SECRETS: List[SecretCheck] = [
    SecretCheck(
        name="JWT_SECRET_KEY",
        placeholder_values=("", "temp-dev-key-change-me", "change-me-in-production"),
        help="Generate with `openssl rand -hex 32` or your secrets manager.",
    ),
    SecretCheck(
        name="GROQ_API_KEY",
        placeholder_values=("", "replace-with-new-groq-key", "gsk_test_key"),
        help="Create a production key in the Groq console and store it in your secret manager.",
    ),
    SecretCheck(
        name="DATABASE_URL",
        placeholder_values=("", "postgresql+psycopg2://postgres:postgres@localhost:5432/finsight"),
        help="Provision a managed Postgres instance and supply the full SQLAlchemy URL.",
    ),
    SecretCheck(
        name="REDIS_URL",
        placeholder_values=("", "redis://localhost:6379", "redis://cache:6379/0"),
        help="Point to your production Redis/KeyDB deployment.",
    ),
    SecretCheck(
        name="ADMIN_KEY",
        placeholder_values=("", "generate-a-random-admin-key", "admin-key-change-me"),
        help="Set a strong random value; required for admin-only endpoints.",
    ),
]

OPTIONAL_SECRETS: List[SecretCheck] = [
    SecretCheck(
        name="OPENAI_API_KEY",
        placeholder_values=("", "sk-dummy"),
        help="Required when using OpenAI fallbacks.",
        optional=True,
    ),
    SecretCheck(
        name="MISTRAL_API_KEY",
        placeholder_values=("", "replace-with-new-mistral-key"),
        help="Needed if the Mistral router is enabled.",
        optional=True,
    ),
    SecretCheck(
        name="COHERE_API_KEY",
        placeholder_values=("", "replace-with-new-cohere-key"),
        help="Needed if Cohere is selected in routing settings.",
        optional=True,
    ),
    SecretCheck(
        name="SEMANTIC_SCHOLAR_API_KEY",
        placeholder_values=("", "replace-with-new-semantic-scholar-key"),
        help="Required for high-volume publication lookups.",
        optional=True,
    ),
    SecretCheck(
        name="GOOGLE_SEARCH_API_KEY",
        placeholder_values=("", "replace-with-new-google-search-key"),
        help="Required for Google Programmable Search integration.",
        optional=True,
    ),
    SecretCheck(
        name="GOOGLE_SEARCH_ENGINE_ID",
        placeholder_values=("", "your-custom-search-engine-id"),
        help="Pair with GOOGLE_SEARCH_API_KEY when enabling web search.",
        optional=True,
    ),
    SecretCheck(
        name="FRED_API_KEY",
        placeholder_values=("",),
        help="Needed for Federal Reserve data ingestion.",
        optional=True,
    ),
    SecretCheck(
        name="OPENALEX_API_KEY",
        placeholder_values=("",),
        help="Recommended for high-rate OpenAlex usage.",
        optional=True,
    ),
    SecretCheck(
        name="SENTRY_DSN",
        placeholder_values=("",),
        help="Optional but recommended for production monitoring.",
        optional=True,
    ),
]


def check_secret(secret: SecretCheck) -> bool:
    value = os.getenv(secret.name)
    if value is None:
        if secret.optional:
            return True
        print(f"❌ {secret.name} is not set", file=sys.stderr)
        print(f"   ➜ {secret.help}", file=sys.stderr)
        return False

    normalised = value.strip()
    if normalised in secret.placeholder_values:
        level = "⚠️" if secret.optional else "❌"
        print(f"{level} {secret.name} is still using a placeholder value", file=sys.stderr)
        print(f"   ➜ {secret.help}", file=sys.stderr)
        return secret.optional

    return True


def main() -> int:
    print("🔐 Running security audit…\n")

    status = True
    for secret in REQUIRED_SECRETS:
        status &= check_secret(secret)

    print()
    for secret in OPTIONAL_SECRETS:
        check_secret(secret)

    print()
    if status:
        print("✅ All required secrets look good. Optional integrations reported above.")
        return 0

    print("❌ Missing or placeholder secrets detected. See guidance above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
