"""Constants, pattern definitions, and supported target mappings for agentignore."""

from typing import Dict, List

# Supported AI tools (12 major AI coding assistants and standards)
SUPPORTED_TARGETS: Dict[str, Dict[str, str]] = {
    "cursor": {
        "name": "Cursor IDE",
        "filename": ".cursorignore",
        "description": "Rules for Cursor Agent, Tab completion, and @ context",
    },
    "claude": {
        "name": "Claude Code",
        "filename": ".claudeignore",
        "description": "Anthropic Claude Code CLI & Desktop Context Filter",
    },
    "cline": {
        "name": "Cline / Roo-Cline",
        "filename": ".clineignore",
        "description": "Autonomous AI coding agent in VSCode",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "filename": ".copilotignore",
        "description": "GitHub Copilot repository content exclusion",
    },
    "windsurf": {
        "name": "Codeium Windsurf",
        "filename": ".windsurfignore",
        "description": "Windsurf Cascade and Supercomplete context exclusion",
    },
    "jetbrains": {
        "name": "JetBrains AI",
        "filename": ".aiignore",
        "description": "JetBrains AI Assistant context exclusion",
    },
    "aider": {
        "name": "Aider",
        "filename": ".aiderignore",
        "description": "Aider pair programming CLI context exclusion",
    },
    "continue": {
        "name": "Continue.dev",
        "filename": ".continueignore",
        "description": "Continue open-source AI code assistant",
    },
    "cody": {
        "name": "Sourcegraph Cody",
        "filename": ".codyignore",
        "description": "Sourcegraph Cody context filtering",
    },
    "gemini": {
        "name": "Gemini Code Assist",
        "filename": ".geminiignore",
        "description": "Google Cloud Gemini Code Assist context filter",
    },
    "opencode": {
        "name": "OpenCode",
        "filename": ".opencodeignore",
        "description": "OpenCode CLI assistant context exclusion",
    },
    "universal": {
        "name": "Universal Agent Standard",
        "filename": ".agentignore",
        "description": "Vendor-agnostic AI agent context specification",
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
