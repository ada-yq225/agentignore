"""Deep content secret scanner for detecting hardcoded API keys and tokens in files."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Optional, Tuple

# Pre-compiled high-confidence secret signatures
SECRET_SIGNATURES: List[Tuple[str, re.Pattern]] = [
    ("OpenAI API Key", re.compile(r"\b(sk-(?!ant-)[a-zA-Z0-9_-]{24,}|sk-proj-[a-zA-Z0-9_-]{30,})\b")),
    ("Anthropic API Key", re.compile(r"\b(sk-ant-[a-zA-Z0-9_-]{30,})\b")),
    ("GitHub Token", re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{50,})\b")),
    ("AWS Access Key ID", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("Slack API Token", re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b")),
    ("Google API Key", re.compile(r"\b(AIza[0-9A-Za-z-_]{35})\b")),
    (
        "Private Cryptographic Key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |)PRIVATE KEY-----"),
    ),
]

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".exe",
    ".bin",
    ".so",
    ".dylib",
    ".dll",
    ".pyc",
    ".class",
    ".wasm",
    ".ttf",
    ".woff",
    ".woff2",
}


@dataclass
class ContentSecretLeak:
    """A hardcoded secret found inside file content."""

    file_path: str
    line_number: int
    secret_type: str
    masked_sample: str


def mask_secret(raw: str) -> str:
    """Mask a secret string for safe display."""
    if len(raw) <= 8:
        return "****"
    return f"{raw[:4]}...{raw[-4:]}"


def is_text_file(path: Path) -> bool:
    """Determine if a file is likely text by extension and initial bytes."""
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return False
        return True
    except Exception:
        return False


def scan_file_content(path: Path, max_bytes: int = 1_000_000) -> List[ContentSecretLeak]:
    """Scan a single text file for leaked credentials and hardcoded keys."""
    leaks: List[ContentSecretLeak] = []
    if not path.is_file() or not is_text_file(path):
        return leaks

    try:
        if path.stat().st_size > max_bytes:
            return leaks
    except OSError:
        return leaks

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, start=1):
                # Quick length check
                if len(line) > 5000:
                    continue
                for secret_type, pattern in SECRET_SIGNATURES:
                    match = pattern.search(line)
                    if match:
                        raw_secret = match.group(0)
                        leaks.append(
                            ContentSecretLeak(
                                file_path=str(path),
                                line_number=line_idx,
                                secret_type=secret_type,
                                masked_sample=mask_secret(raw_secret),
                            )
                        )
    except Exception:
        pass

    return leaks
