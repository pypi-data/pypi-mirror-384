import pytest
from unittest.mock import MagicMock, patch
from clutchtimealerts.clutch_alerts import ClutchAlertsService
from clutchtimealerts.notifications.base import NotificationConfig


@pytest.fixture
def mock_notification_config():
    config = MagicMock(spec=NotificationConfig)
    config.nba_teams = ["LAL", "BOS"]
    config.preseason = False
    config.notification_format = "clutch format"
    config.ot_format = "ot format"
    config.notification = MagicMock()
    config.notification.send = MagicMock()
    return config


@pytest.fixture
def sample_game():
    return {
        "gameId": "12345",
        "homeTeam": {"teamTricode": "LAL", "score": 100},
        "awayTeam": {"teamTricode": "BOS", "score": 98},
        "period": 4,
        "gameClock": "PT04M30S",
        "gameLabel": "Regular Season",
    }


def test_get_minutes_from_clock_valid():
    service = ClutchAlertsService([])
    assert service._get_minutes_from_clock("PT04M30S") == 4
    assert service._get_minutes_from_clock("PT12M00S") == 12


def test_get_minutes_from_clock_invalid():
    service = ClutchAlertsService([])
    assert service._get_minutes_from_clock("") == -1
    assert service._get_minutes_from_clock("INVALID") == -1


def test_is_clutch_time_true(sample_game):
    service = ClutchAlertsService([])
    assert service.isCluthTime(sample_game) is True


def test_is_clutch_time_false_period(sample_game):
    service = ClutchAlertsService([])
    sample_game["period"] = 3
    assert service.isCluthTime(sample_game) is False


def test_is_clutch_time_false_minutes(sample_game):
    service = ClutchAlertsService([])
    sample_game["gameClock"] = "PT06M00S"
    assert service.isCluthTime(sample_game) is False


def test_is_clutch_time_false_score_diff(sample_game):
    service = ClutchAlertsService([])
    sample_game["awayTeam"]["score"] = 90
    assert service.isCluthTime(sample_game) is False


def test_is_preseason_true(sample_game):
    service = ClutchAlertsService([])
    sample_game["gameLabel"] = "Preseason"
    assert service.isPreseason(sample_game) is True


def test_is_preseason_false(sample_game):
    service = ClutchAlertsService([])
    assert service.isPreseason(sample_game) is False


def test_is_overtime_true(sample_game):
    service = ClutchAlertsService([])
    sample_game["period"] = 5
    assert service.isOvertime(sample_game) is True


def test_is_overtime_false(sample_game):
    service = ClutchAlertsService([])
    sample_game["period"] = 4
    assert service.isOvertime(sample_game) is False


@patch("clutchtimealerts.clutch_alerts.format_message")
def test_send_alert_clutch(mock_format_message, mock_notification_config, sample_game):
    mock_format_message.return_value = "formatted message"
    service = ClutchAlertsService([mock_notification_config])

    service.send_alert(sample_game, "clutch")

    mock_format_message.assert_called_once_with(
        sample_game, mock_notification_config.notification_format
    )
    mock_notification_config.notification.send.assert_called_once_with(
        "formatted message"
    )


@patch("clutchtimealerts.clutch_alerts.format_message")
def test_send_alert_ot(mock_format_message, mock_notification_config, sample_game):
    mock_format_message.return_value = "ot message"
    service = ClutchAlertsService([mock_notification_config])

    service.send_alert(sample_game, "ot")

    mock_format_message.assert_called_once_with(
        sample_game, mock_notification_config.ot_format
    )
    mock_notification_config.notification.send.assert_called_once_with("ot message")


def test_send_alert_skips_non_teams(mock_notification_config, sample_game):
    service = ClutchAlertsService([mock_notification_config])
    sample_game["homeTeam"]["teamTricode"] = "NYK"
    sample_game["awayTeam"]["teamTricode"] = "MIA"

    service.send_alert(sample_game, "clutch")

    mock_notification_config.notification.send.assert_not_called()


def test_send_alert_skips_non_preseason(mock_notification_config, sample_game):
    service = ClutchAlertsService([mock_notification_config])
    sample_game["gameLabel"] = "Preason"

    service.send_alert(sample_game, "clutch")

    mock_notification_config.notification.send.assert_not_called()


@patch("clutchtimealerts.clutch_alerts.format_message")
def test_send_alert_sends_if_preseason_enabled(
    mock_format_message, mock_notification_config, sample_game
):
    mock_format_message.return_value = "formatted message"
    mock_notification_config.preseason = True

    service = ClutchAlertsService([mock_notification_config])

    sample_game["gameLabel"] = "Preason"
    service.send_alert(sample_game, "clutch")

    mock_format_message.assert_called_once_with(
        sample_game, mock_notification_config.notification_format
    )
    mock_notification_config.notification.send.assert_called_once_with(
        "formatted message"
    )
