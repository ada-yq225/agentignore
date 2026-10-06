"""Constants, standard pattern definitions, and target mappings for agentignore."""

from typing import Dict, List

# Supported AI tools and their specific ignore files
SUPPORTED_TARGETS: Dict[str, Dict[str, str]] = {
    "cursor": {
        "name": "Cursor",
        "filename": ".cursorignore",
        "description": "Cursor AI IDE (Rules for Agent, Tab, and context search)",
    },
    "claude": {
        "name": "Claude Code",
        "filename": ".claudeignore",
        "description": "Anthropic Claude Code CLI & Desktop",
    },
    "cline": {
        "name": "Cline / Roo-Cline",
        "filename": ".clineignore",
        "description": "Autonomous AI coding agent in VSCode",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "filename": ".copilotignore",
        "description": "GitHub Copilot context exclusion",
    },
    "windsurf": {
        "name": "Windsurf",
        "filename": ".windsurfignore",
        "description": "Codeium Windsurf IDE Cascade context",
    },
    "jetbrains": {
        "name": "JetBrains AI",
        "filename": ".aiignore",
        "description": "JetBrains AI Assistant context exclusion",
    },
    "universal": {
        "name": "Universal Agent Standard",
        "filename": ".agentignore",
        "description": "Vendor-agnostic AI agent ignore specification",
    },
}

TARGET_FILENAME_MAP: Dict[str, str] = {
    key: info["filename"] for key, info in SUPPORTED_TARGETS.items()
}

FILENAME_TO_TARGET_MAP: Dict[str, str] = {
    info["filename"]: key for key, info in SUPPORTED_TARGETS.items()
}

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
    "*.crt",
    "*.cer",
    "*.der",
    # SSH keys
    "id_rsa",
    "id_rsa.pub",
    "id_ed25519",
    "id_ed25519.pub",
    "id_ecdsa*",
    "id_dsa*",
    # Cloud and API credentials
    "*credentials*.json",
    "*service-account*.json",
    "*secret*.json",
    "*.token",
    ".aws/credentials",
    ".gcp/*.json",
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

# Lockfiles: Can be 10,000 ~ 100,000+ tokens, massive bloat when fed to LLMs
LOCKFILE_PATTERNS: List[str] = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "composer.lock",
    "Gemfile.lock",
]
