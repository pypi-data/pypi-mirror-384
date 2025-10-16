from asyncio import subprocess
import pytest
from unittest.mock import patch, MagicMock
import sys

@pytest.fixture
def mock_main():
    with patch('weathergrabber.cli.weathergrabber.main') as m:
        yield m

def test_cli_location_name(monkeypatch, mock_main):
    test_args = ["weathergrabber", "London"]
    monkeypatch.setattr(sys, "argv", test_args)
    from weathergrabber.cli import main_cli
    main_cli()
    mock_main.assert_called_once()
    args = mock_main.call_args[1]
    assert args["location_name"] == "London"
    assert args["output"] == "console"
    assert args["icons"] == "emoji"


def test_cli_location_id(monkeypatch, mock_main):
    test_args = ["weathergrabber", "--location-id", "abcdef123456"]
    monkeypatch.setattr(sys, "argv", test_args)
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["location_id"] == "abcdef123456"


def test_cli_output_json(monkeypatch, mock_main):
    test_args = ["weathergrabber", "Paris", "--output", "json"]
    monkeypatch.setattr(sys, "argv", test_args)
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["output"] == "json"


def test_cli_icons_fa(monkeypatch, mock_main):
    test_args = ["weathergrabber", "Berlin", "--icons", "fa"]
    monkeypatch.setattr(sys, "argv", test_args)
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["icons"] == "fa"


def test_cli_keep_open(monkeypatch, mock_main):
    test_args = ["weathergrabber", "Madrid", "--keep-open"]
    monkeypatch.setattr(sys, "argv", test_args)
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["keep_open"] is True


def test_cli_lang_env(monkeypatch, mock_main):
    test_args = ["weathergrabber", "Rome"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setenv("LANG", "fr_FR.UTF-8")
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["lang"] == "fr-FR"


def test_cli_location_id_env(monkeypatch, mock_main):
    test_args = ["weathergrabber"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setenv("WEATHER_LOCATION_ID", "envlocationid")
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["location_id"] == "envlocationid"

def test_cli_log_level(monkeypatch, mock_main):
    test_args = ["weathergrabber", "Tokyo", "--log", "debug"]
    monkeypatch.setattr(sys, "argv", test_args)
    from weathergrabber.cli import main_cli
    main_cli()
    args = mock_main.call_args[1]
    assert args["log_level"] == "debug"