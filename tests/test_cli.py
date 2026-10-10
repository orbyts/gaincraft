from __future__ import annotations

import json

from typer.testing import CliRunner

from luvix import __version__
from luvix.cli import app

runner = CliRunner()


def test_version_is_exact() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout == f"luvix {__version__}\n"


def test_doctor_reports_bootstrap_scope() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Bootstrap CLI" in result.stdout
    assert "Python" in result.stdout
    assert "uhdrload" in result.stdout
    assert "uhdrsave" in result.stdout
    assert "HDR processing begins in Luvix 0.0.2." in result.stdout


def test_doctor_json_has_stable_contract() -> None:
    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["luvix"] == {"release": "bootstrap", "version": __version__}
    assert payload["bootstrap"] == {"ready": True}
    assert payload["hdr_processing"]["implemented"] is False
    assert payload["hdr_processing"]["begins_in"] == "0.0.2"
    assert set(payload["ultrahdr"]) == {"library_discoverable", "uhdrload", "uhdrsave"}


def test_doctor_never_prints_cloudinary_credentials(monkeypatch) -> None:
    secrets = {
        "CLOUDINARY_CLOUD_NAME": "private-cloud",
        "CLOUDINARY_API_KEY": "private-key",
        "CLOUDINARY_API_SECRET": "private-secret",
    }
    for name, value in secrets.items():
        monkeypatch.setenv(name, value)

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["cloudinary"]["credentials_configured"] is True
    assert all(secret not in result.stdout for secret in secrets.values())


def test_no_args_shows_help() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 2
    assert "Inspect, extract, rebuild, validate, and convert HDR gain-map images." in result.stdout
