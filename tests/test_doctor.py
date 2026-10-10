from __future__ import annotations

from luvix.doctor import _cloudinary_credentials_configured


def test_partial_cloudinary_credentials_are_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("CLOUDINARY_URL", raising=False)
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "cloud")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "key")
    monkeypatch.delenv("CLOUDINARY_API_SECRET", raising=False)

    assert _cloudinary_credentials_configured() is False


def test_cloudinary_url_counts_as_configured(monkeypatch) -> None:
    monkeypatch.setenv("CLOUDINARY_URL", "cloudinary://key:secret@example")

    assert _cloudinary_credentials_configured() is True
