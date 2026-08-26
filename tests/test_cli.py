import pytest

from acri.cli import main


def test_version_flag_reports_the_installed_pyacri_version(monkeypatch, capsys):
    monkeypatch.setattr("acri.cli.version", lambda name: "9.9.9")
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out.strip() == "acri 9.9.9"


def test_version_flag_falls_back_to_dev_when_not_installed(monkeypatch):
    from importlib.metadata import PackageNotFoundError

    def raise_not_found(name):
        raise PackageNotFoundError(name)

    monkeypatch.setattr("acri.cli.version", raise_not_found)
    with pytest.raises(SystemExit):
        main(["-V"])


def test_bare_invocation_shows_help_instead_of_erroring(capsys):
    """The first thing a new user types after installing is often just `acri`
    with nothing else -- that should explain itself, not exit with an argparse
    error (it did, before this test)."""
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "usage: acri" in out
    assert "studio" in out  # every subcommand should be listed


def test_init_writes_a_template(tmp_path):
    path = tmp_path / "acri.yaml"
    assert main(["init", str(path)]) == 0
    assert "version: 1" in path.read_text(encoding="utf-8")


def test_init_refuses_to_overwrite_an_existing_file(tmp_path):
    path = tmp_path / "acri.yaml"
    path.write_text("version: 1\n", encoding="utf-8")
    assert main(["init", str(path)]) == 1
    assert path.read_text(encoding="utf-8") == "version: 1\n"  # untouched


def test_check_reports_missing_credentials(tmp_path, monkeypatch):
    path = tmp_path / "acri.yaml"
    path.write_text("version: 1\nmodels:\n  default: gemini-2.5-flash\n", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert main(["check", str(path)]) == 1


def test_check_passes_when_credentials_are_present(tmp_path, monkeypatch):
    path = tmp_path / "acri.yaml"
    path.write_text("version: 1\nmodels:\n  default: gemini-2.5-flash\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    assert main(["check", str(path)]) == 0


def test_check_fails_on_a_missing_file(tmp_path):
    assert main(["check", str(tmp_path / "nope.yaml")]) == 1


def test_up_fails_cleanly_on_a_missing_config_instead_of_a_traceback(tmp_path, monkeypatch, capsys):
    """The bug this regression-tests: `acri up`/`acri studio` used to let
    FileNotFoundError escape all the way to a raw Python traceback."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main(["up", str(tmp_path / "nope.yaml")]) == 1
    assert "run `acri init` first" in capsys.readouterr().err


def test_studio_fails_cleanly_on_a_missing_config_instead_of_a_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    assert main(["studio", str(tmp_path / "nope.yaml")]) == 1
    assert "run `acri init` first" in capsys.readouterr().err
