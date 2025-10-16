from clutchtimealerts.notifications.base import NotificationConfig
from clutchtimealerts.format_utils import format_message, mock_game
import yaml
import logging

logger = logging.getLogger("clutchtimealerts")

DEFAULT_NOTIFICATION_FORMAT = "Clutch Game\n{HOME_TEAM_TRI} {HOME_TEAM_SCORE} - {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}\n{NBA_COM_STREAM}"
DEFAULT_OT_FORMAT = "OT{OT_NUMBER} Alert\n{HOME_TEAM_TRI} {HOME_TEAM_SCORE} - {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}\n{NBA_COM_STREAM}"
NBA_TRICODES = {
    "ATL",  # Atlanta Hawks
    "BOS",  # Boston Celtics
    "BKN",  # Brooklyn Nets
    "CHA",  # Charlotte Hornets
    "CHI",  # Chicago Bulls
    "CLE",  # Cleveland Cavaliers
    "DAL",  # Dallas Mavericks
    "DEN",  # Denver Nuggets
    "DET",  # Detroit Pistons
    "GSW",  # Golden State Warriors
    "HOU",  # Houston Rockets
    "IND",  # Indiana Pacers
    "LAC",  # Los Angeles Clippers
    "LAL",  # Los Angeles Lakers
    "MEM",  # Memphis Grizzlies
    "MIA",  # Miami Heat
    "MIL",  # Milwaukee Bucks
    "MIN",  # Minnesota Timberwolves
    "NOP",  # New Orleans Pelicans
    "NYK",  # New York Knicks
    "OKC",  # Oklahoma City Thunder
    "ORL",  # Orlando Magic
    "PHI",  # Philadelphia 76ers
    "PHX",  # Phoenix Suns
    "POR",  # Portland Trail Blazers
    "SAC",  # Sacramento Kings
    "SAS",  # San Antonio Spurs
    "TOR",  # Toronto Raptors
    "UTA",  # Utah Jazz
    "WAS",  # Washington Wizards
}
DEFAULT_PRESEASON = False


class ConfigParser:
    def __init__(
        self,
        config_path: str = "config.yaml",
        classname_dict: dict = {},
        common_name_dict: dict = {},
    ) -> None:
        self.config_path = config_path
        self.classname_dict = classname_dict
        self.common_name_dict = common_name_dict

    def parse_config(self) -> None:
        # Parse YAML Config
        with open(self.config_path, "r") as f:
            config: dict = yaml.safe_load(f)

        # Parse database file path
        self.db_url = config.get("db_url", "sqlite:///clutchtime.db")

        # Parse Notifcation Format
        notification_format = config.get(
            "notification_format", DEFAULT_NOTIFICATION_FORMAT
        )
        ot_format = config.get("ot_format", DEFAULT_OT_FORMAT)
        team_config = set(config.get("nba_teams", NBA_TRICODES))
        preseason = config.get("preseason", DEFAULT_PRESEASON)

        notification_yaml: list[dict] = config.get("notifications", [])
        self.notification_configs = []
        for notify_config in notification_yaml:
            if "type" not in notify_config:
                raise ValueError("Notification type must be specified in config file")

            # Get YAML Config
            notifiction_type = notify_config["type"]
            class_config = notify_config["config"]
            notification_team_config = NBA_TRICODES.intersection(
                set(notify_config.get("nba_teams", team_config))
            )

            if len(notification_team_config) == 0:
                logger.warning(
                    f"No teams specified for notification type {notifiction_type} defaulting to all teams"
                )
                notification_team_config = NBA_TRICODES

            # Check that notification type exists
            if notifiction_type in self.classname_dict:
                notification_class = self.classname_dict[notifiction_type]
            elif notifiction_type in self.common_name_dict:
                notification_class = self.common_name_dict[notifiction_type]
            else:
                logger.warning(
                    f"Unknown notification type: {notifiction_type} ... skipping"
                )
                continue

            # Instatiate Notification
            try:
                notification_instance = notification_class(**class_config)
            except Exception as e:
                logger.warning(
                    f"Failed to create notification of type {notifiction_type}: {e} ... skipping"
                )
                continue

            try:
                format_message(
                    mock_game,
                    notify_config.get("notification_format", notification_format),
                )
                format_message(mock_game, notify_config.get("ot_format", ot_format))
            except Exception as e:
                logger.warning(
                    f"Failed to create formatter for notification of type {notifiction_type}: {e} ... skipping"
                )
                continue

            # Create notification config
            notification_config = NotificationConfig(
                notification=notification_instance,
                notification_format=notify_config.get(
                    "notification_format", notification_format
                ),
                ot_format=notify_config.get("ot_format", ot_format),
                nba_teams=notification_team_config,
                preseason=notify_config.get("preseason", preseason),
            )
            self.notification_configs.append(notification_config)

        if len(self.notification_configs) == 0:
            raise ValueError("No notifications found in config file")
