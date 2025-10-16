import pytest
from unittest.mock import patch, mock_open, MagicMock
from clutchtimealerts.config_parser import (
    ConfigParser,
    DEFAULT_NOTIFICATION_FORMAT,
    DEFAULT_OT_FORMAT,
    DEFAULT_PRESEASON,
    NBA_TRICODES,
)
from clutchtimealerts.notifications.base import Notification


class MockNotification(Notification):
    COMMON_NAME = "mock_notification"

    def __init__(self, *args, **kwargs):
        super().__init__()
        raise ImportError("Mocked import error")

    def send(self, message):
        pass


@pytest.fixture
def sample_config():
    """Fixture for a sample configuration YAML."""
    return """
    db_url: "test.db"
    notifications:
      - type: email
        config:
          recipient: "test@example.com"
      - type: sms
        config:
          phone_number: "+123456789"
    """


@pytest.fixture
def classname_dict():
    """Fixture for mock classname dictionary."""
    return {
        "email": MagicMock(return_value="EmailNotificationInstance"),
        "sms": MagicMock(return_value="SMSNotificationInstance"),
        "mock_notification": MockNotification,
    }


@pytest.fixture
def common_name_dict():
    """Fixture for mock common name dictionary."""
    return {
        "text": MagicMock(return_value="TextNotificationInstance"),
    }


@patch("builtins.open", new_callable=mock_open)
@patch("yaml.safe_load")
def test_parse_config_valid_config(
    mock_yaml_load, mock_open_file, sample_config, classname_dict, common_name_dict
):
    """Test parsing a valid configuration file."""
    mock_yaml_load.return_value = {
        "db_url": "test.db",
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }

    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    # Check database path and table name
    assert parser.db_url == "test.db"

    # Check notification_configs
    assert len(parser.notification_configs) == 2
    assert classname_dict["email"].call_count == 1
    assert classname_dict["sms"].call_count == 1


@patch("builtins.open", new_callable=mock_open)
@patch("yaml.safe_load")
@patch("clutchtimealerts.config_parser.logger.warning")
def test_parse_config_invalid_notification_type(
    mock_warning,
    mock_yaml_load,
    mock_open_file,
    sample_config,
    classname_dict,
    common_name_dict,
):
    """Test config with invalid notification type."""
    mock_yaml_load.return_value = {
        "notifications": [
            {"type": "unknown_type", "config": {}},
        ],
    }

    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )

    try:
        parser.parse_config()
    except ValueError:
        assert True
    except Exception:
        assert False

    # Check that no notification_configs are created
    assert len(parser.notification_configs) == 0

    # Check that the logger was called with a warning
    mock_warning.assert_called_with(
        "Unknown notification type: unknown_type ... skipping"
    )


@patch("builtins.open", new_callable=mock_open)
@patch("yaml.safe_load")
def test_parse_config_missing_notification_type(
    mock_yaml_load, mock_open_file, sample_config
):
    """Test config missing notification type."""
    mock_yaml_load.return_value = {
        "notifications": [
            {"config": {"recipient": "test@example.com"}},
        ],
    }

    parser = ConfigParser(config_path="test_config.yaml")

    with pytest.raises(
        ValueError, match="Notification type must be specified in config file"
    ):
        parser.parse_config()


@patch("builtins.open", new_callable=mock_open)
@patch("yaml.safe_load")
def test_parse_config_no_notifications(mock_yaml_load, mock_open_file):
    """Test config with no notifications."""
    mock_yaml_load.return_value = {}

    parser = ConfigParser(config_path="test_config.yaml")

    with pytest.raises(ValueError, match="No notifications found in config file"):
        parser.parse_config()


@patch("builtins.open", new_callable=mock_open)
@patch("yaml.safe_load")
@patch("clutchtimealerts.config_parser.logger.warning")
def test_parse_config_invalid_notification_config(
    mock_warning, mock_yaml_load, mock_open_file, classname_dict
):
    """Test config with invalid notification configuration."""
    # Simulate invalid configuration for notifications
    mock_yaml_load.return_value = {
        "notifications": [
            {
                "type": "mock_notification",
                "config": {"invalid_param": "value"},
            },  # Invalid config
        ],
    }

    parser = ConfigParser(config_path="test_config.yaml", classname_dict=classname_dict)

    # Call the method to parse the config
    try:
        parser.parse_config()
    except ValueError:
        assert True
    except Exception:
        assert False

    # Check that no notifications are created
    assert len(parser.notification_configs) == 0

    # Check that the logger was called with the correct warning
    mock_warning.assert_any_call(
        "Failed to create notification of type mock_notification: Mocked import error ... skipping"
    )


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_config_missing_db_url(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with missing db_url."""
    mock_yaml_load.return_value = {
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.db_url == "sqlite:///clutchtime.db"


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_default_notification_format(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert (
        parser.notification_configs[0].notification_format
        == DEFAULT_NOTIFICATION_FORMAT
    )
    assert (
        parser.notification_configs[1].notification_format
        == DEFAULT_NOTIFICATION_FORMAT
    )
    assert parser.notification_configs[0].ot_format == DEFAULT_OT_FORMAT
    assert parser.notification_configs[1].ot_format == DEFAULT_OT_FORMAT


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_config_global_notification_format(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with global notifications."""
    mock_yaml_load.return_value = {
        "notification_format": "test_format",
        "ot_format": "test_ot_format",
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].notification_format == "test_format"
    assert parser.notification_configs[1].notification_format == "test_format"
    assert parser.notification_configs[0].ot_format == "test_ot_format"
    assert parser.notification_configs[1].ot_format == "test_ot_format"


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_config_type_notification_format(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with type specific notification formats."""
    mock_yaml_load.return_value = {
        "notification_format": "test_format",
        "ot_format": "test_ot_format",
        "notifications": [
            {
                "type": "email",
                "notification_format": "test_format2",
                "config": {"recipient": "test@example.com"},
            },
            {
                "type": "sms",
                "ot_format": "test_ot_format2",
                "config": {"phone_number": "+123456789"},
            },
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].notification_format == "test_format2"
    assert parser.notification_configs[1].notification_format == "test_format"
    assert parser.notification_configs[0].ot_format == "test_ot_format"
    assert parser.notification_configs[1].ot_format == "test_ot_format2"


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
@patch("clutchtimealerts.config_parser.logger.warning")
def test_parse_config_invalid_notification_format(
    mock_warning, mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    mock_yaml_load.return_value = {
        "notifications": [
            {
                "type": "email",
                "notification_format": "{NOT_REAL_VALUE}",
                "config": {"recipient": "test@example.com"},
            },
        ],
    }

    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    try:
        parser.parse_config()
    except Exception:
        assert True
    else:
        assert False

    mock_warning.assert_called_once_with(
        "Failed to create formatter for notification of type email: 'NOT_REAL_VALUE' ... skipping"
    )


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
@patch("clutchtimealerts.config_parser.logger.warning")
def test_parse_config_invalid_ot_format(
    mock_warning, mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    mock_yaml_load.return_value = {
        "notifications": [
            {
                "type": "email",
                "ot_format": "{NOT_REAL_VALUE}",
                "config": {"recipient": "test@example.com"},
            },
        ],
    }

    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    try:
        parser.parse_config()
    except Exception:
        assert True
    else:
        assert False

    mock_warning.assert_called_once_with(
        "Failed to create formatter for notification of type email: 'NOT_REAL_VALUE' ... skipping"
    )


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_default_nba_teams(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].nba_teams == NBA_TRICODES
    assert parser.notification_configs[1].nba_teams == NBA_TRICODES


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_default_preseason(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].preseason == DEFAULT_PRESEASON
    assert parser.notification_configs[1].preseason == DEFAULT_PRESEASON


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_global_nba_teams(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "nba_teams": {"PHI", "BOS", "MIA"},
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].nba_teams == {"PHI", "BOS", "MIA"}
    assert parser.notification_configs[1].nba_teams == {"PHI", "BOS", "MIA"}


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_notify_specific_nba_teams(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "nba_teams": {"PHI", "BOS", "MIA"},
        "notifications": [
            {
                "type": "email",
                "nba_teams": {"MIL"},
                "config": {"recipient": "test@example.com"},
            },
            {
                "type": "sms",
                "nba_teams": {"NOP"},
                "config": {"phone_number": "+123456789"},
            },
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].nba_teams == {"MIL"}
    assert parser.notification_configs[1].nba_teams == {"NOP"}


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
@patch("clutchtimealerts.config_parser.logger.warning")
def test_parse_invalid_specific_nba_teams(
    mock_warning, mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "nba_teams": {"PHI", "BOS", "MIA"},
        "notifications": [
            {
                "type": "email",
                "nba_teams": {"FAK"},
                "config": {"recipient": "test@example.com"},
            },
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].nba_teams == NBA_TRICODES

    mock_warning.assert_called_once_with(
        "No teams specified for notification type email defaulting to all teams"
    )


@patch("yaml.safe_load")
@patch("builtins.open", new_callable=mock_open)
def test_parse_global_preseason(
    mock_open_file, mock_yaml_load, classname_dict, common_name_dict
):
    """Test config with no notification format."""
    mock_yaml_load.return_value = {
        "preseason": True,
        "notifications": [
            {"type": "email", "config": {"recipient": "test@example.com"}},
            {"type": "sms", "config": {"phone_number": "+123456789"}},
        ],
    }
    parser = ConfigParser(
        config_path="test_config.yaml",
        classname_dict=classname_dict,
        common_name_dict=common_name_dict,
    )
    parser.parse_config()

    assert parser.notification_configs[0].preseason
    assert parser.notification_configs[1].preseason
