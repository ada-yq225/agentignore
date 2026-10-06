"""Constants, pattern definitions, and supported target mappings for agentignore."""

from typing import Dict, List

# Only documented, implemented adapters are advertised.
SUPPORTED_TARGETS: Dict[str, Dict[str, str]] = {
    "codex": {"name": "Codex", "filename": ".codex/config.toml",
              "description": "Local sandbox permission profile (beta)"},
    "claude": {"name": "Claude Code", "filename": ".claude/settings.json",
               "description": "Built-in Read/Edit deny rules"},
}
TARGET_FILENAME_MAP = {key: info["filename"] for key, info in SUPPORTED_TARGETS.items()}
FILENAME_TO_TARGET_MAP = {v: k for k, v in TARGET_FILENAME_MAP.items()}

# Critical security and secret patterns that must never be read by AI models
SENSITIVE_PATTERNS: List[str] = [
    # Environment variables & secrets
    ".env",
    ".env.*",
    "*.env",
    ".env.local",
    ".env.development.local",
    ".env.test.local",
    ".env.production.local",
    # Cryptographic keys and certificates
    "*.pem",
    "*.key",
    "*.pkcs12",
    "*.pfx",
    "*.p12",
    # SSH keys
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
    "id_dsa",
    # Cloud and API credentials
    "*credentials*.json",
    "*service-account*.json",
    "*secret*.json",
    "*.token",
    ".aws/credentials",
    ".aws/config",
    ".gcp/*.json",
    ".kube/config",
    # Mobile and application signing keystores
    "*.keystore",
    "*.jks",
]

# Patterns that waste excessive tokens and degrade LLM performance
DEFAULT_BLOAT_PATTERNS: List[str] = [
    # Dependencies & vendor trees
    "node_modules/",
    "bower_components/",
    "vendor/",
    ".venv/",
    "venv/",
    "env/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    # Build outputs & distribution artifacts
    "dist/",
    "build/",
    "out/",
    "target/",
    "bin/",
    "obj/",
    ".next/",
    ".nuxt/",
    ".output/",
    ".docusaurus/",
    ".astro/",
    "*.egg-info/",
    # Bundles, minified files & source maps
    "*.min.js",
    "*.min.css",
    "*.bundle.js",
    "*.map",
    # Test coverage & tooling caches
    "coverage/",
    ".nyc_output/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".tox/",
    ".turbo/",
    ".cache/",
    # Database files & backups
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.sql.gz",
    "*.dump",
    # Log files
    "*.log",
    "logs/",
    "npm-debug.log*",
    "yarn-debug.log*",
    "yarn-error.log*",
    "pnpm-debug.log*",
    # OS generated noise
    ".DS_Store",
    "Thumbs.db",
]

# Lockfiles: Can be 10,000 ~ 100,000+ tokens
LOCKFILE_PATTERNS: List[str] = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "composer.lock",
    "Gemfile.lock",
]
