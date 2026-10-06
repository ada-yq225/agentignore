"""Tests for deep content secret scanner."""

from pathlib import Path
from agentignore.scanner import mask_secret, scan_file_content


def test_mask_secret():
    assert mask_secret("sk-1234567890abcdef") == "sk-1...cdef"
    assert mask_secret("short") == "****"


def test_detects_openai_api_key_in_file(tmp_path: Path):
    source_file = tmp_path / "config.js"
    source_file.write_text("const apiKey = 'sk-proj-abc1234567890abcdef1234567890';", encoding="utf-8")

    leaks = scan_file_content(source_file)
    assert len(leaks) == 1
    assert leaks[0].secret_type == "OpenAI API Key"
    assert leaks[0].line_number == 1
    assert "sk-p...7890" in leaks[0].masked_sample


def test_detects_aws_key_in_file(tmp_path: Path):
    source_file = tmp_path / "aws_deploy.py"
    source_file.write_text('AWS_KEY = "AKIA1234567890ABCDEF"\nprint("deploying")', encoding="utf-8")

    leaks = scan_file_content(source_file)
    assert len(leaks) == 1
    assert leaks[0].secret_type == "AWS Access Key ID"
    assert leaks[0].line_number == 1


def test_detects_private_key_header(tmp_path: Path):
    cert_file = tmp_path / "custom_key.txt"
    cert_file.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...", encoding="utf-8")

    leaks = scan_file_content(cert_file)
    assert len(leaks) == 1
    assert leaks[0].secret_type == "Private Cryptographic Key"


def test_skips_binary_files(tmp_path: Path):
    bin_file = tmp_path / "image.png"
    bin_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRsk-1234567890abcdef")

    leaks = scan_file_content(bin_file)
    assert len(leaks) == 0
