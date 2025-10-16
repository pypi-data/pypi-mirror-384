import time
import requests
import logging

from clutchtimealerts.scraper.live_scores import NBAScoreScraper
from clutchtimealerts.notifications.base import NotificationConfig
from clutchtimealerts.format_utils import format_message
from clutchtimealerts.db_utils import (
    get_engine,
    check_and_recreate_table,
    clear_table,
    insert_game,
    check_alert_sent,
    update_alert_sent,
    check_overtime_alert_sent,
    update_overtime_number,
)

logger = logging.getLogger("clutchtimealerts")


class ClutchAlertsService:
    def __init__(
        self,
        notification_configs: list[NotificationConfig],
        db_url: str = "sqlite:///clutchtime.db",
    ) -> None:
        self.scraper = NBAScoreScraper()
        self.notification_configs = notification_configs
        self.db_url = db_url

    def send_alert(self, game: dict, alert_type: str) -> None:
        """
        Send the given message as notification.

        Parameters
        ----------
        game: dict
            The game json data to send as a message
        alert_type : str
            The type of message to send ("ot" or "clutch")

        Returns
        -------
        None
        """
        for notification_config in self.notification_configs:
            # Skip games not for specified teams
            if (
                game["homeTeam"]["teamTricode"] not in notification_config.nba_teams
                and game["awayTeam"]["teamTricode"] not in notification_config.nba_teams
            ):
                logger.debug(
                    f"Skipping notification for {notification_config.notification.__class__.__name__} as it is not in the nba teams"
                )
                continue

            # Skip if game is in the preseason and the notification configuration is not for the preseason
            if self.isPreseason(game) and not notification_config.preseason:
                logger.debug(
                    f"Skipping notification for {notification_config.notification.__class__.__name__} as it is a preseason game"
                )
                continue

            try:
                if alert_type == "ot":
                    message = format_message(game, notification_config.ot_format)
                elif alert_type == "clutch":
                    message = format_message(
                        game, notification_config.notification_format
                    )
            except Exception:
                logger.error(
                    f"Error formatting message for {notification_config.notification.__class__.__name__}"
                )
                continue

            # Send message with notification
            logger.debug(f"Sending message: {message}")
            try:
                notification_config.notification.send(message)
            except Exception as e:
                logger.error(
                    f"Error sending notification to {notification_config.notification.__class__.__name__}: {e}"
                )

    def _get_minutes_from_clock(self, clock) -> int:
        """
        Extract the minutes from the given clock string.

        The clock string is expected to be in the format "PT{minutes}M{seconds}S"
        If the string is empty or not in this format, -1 is returned.

        Parameters
        ----------
        clock : str
            The clock string to extract the minutes from.

        Returns
        -------
        int
            The minutes if the string is in the correct format, otherwise -1.
        """
        try:
            return int(clock.split("PT")[1].split("M")[0])
        except Exception:
            return -1

    def isCluthTime(self, game: dict) -> bool:
        """
        Checks if the given game is in "clutch time" - the last five minutes of the fourth quarter
        or overtime with the point difference being five points or fewer.

        Parameters
        ----------
        game : dict
            The game data to check.

        Returns
        -------
        bool
            True if the game is in clutch time, otherwise False.
        """
        period = game["period"]
        homeTeamScore = game["homeTeam"]["score"]
        awayTeamScore = game["awayTeam"]["score"]
        clock = game["gameClock"]
        minutes = self._get_minutes_from_clock(clock)

        if period < 4:
            return False
        elif minutes == -1 or minutes >= 5:
            return False
        elif abs(homeTeamScore - awayTeamScore) > 5:
            return False

        return True

    def isPreseason(self, game: dict) -> bool:
        """
        Checks if the given game is preseason game.

        Parameters
        ----------
        game : dict
            The game data to check.

        Returns
        -------
        bool
            True if the game is an overtime game, otherwise False.
        """
        return game["gameLabel"] == "Preseason"

    def isOvertime(self, game: dict) -> bool:
        """
        Checks if the given game is in overtime.

        Parameters
        ----------
        game : dict
            The game data to check.

        Returns
        -------
        bool
            True if the game is in overtime, otherwise False.
        """
        return game["period"] > 4

    def run(self) -> None:
        """
        Run the ClutchAlertsService to continuously monitor NBA games and send alerts.

        This method initializes the database and enters an infinite loop to fetch
        live NBA games. It checks each game's status to determine if it is in "clutch time,"
        and sends alerts for such games. If there are no live games, it sleeps for 2 hours.

        Returns
        -------
        None
        """
        # Create the database
        Session, engine = get_engine(self.db_url)
        check_and_recreate_table(engine)
        while True:
            # Fetch live games
            try:
                games = self.scraper.live_games()
                logger.info(f"Fetched {len(games)} live games")
            except requests.exceptions.ConnectionError:
                logger.error("Failed to fetch live games. Retrying...")
                time.sleep(60)
                continue

            # Iterate through each live game and send alert
            for game in games:
                gameId = game["gameId"]
                homeTeam = game["homeTeam"]["teamTricode"]
                awayTeam = game["awayTeam"]["teamTricode"]
                game["nbaComStream"] = (
                    f"https://www.nba.com/game/{awayTeam}-vs-{homeTeam}-{gameId}?watchLive=true"
                )
                if self.isOvertime(game):
                    overtime_number = game["period"] - 4
                    logger.info(
                        f"Overtime Game detected: OT{overtime_number} {awayTeam} v {homeTeam} - checking db"
                    )
                    if not check_overtime_alert_sent(
                        Session,
                        game["gameId"],
                        overtime_number,
                    ):
                        logger.info(
                            f"Alerting for Overtime Game: OT{overtime_number} {awayTeam} v {homeTeam}"
                        )
                        self.send_alert(game, "ot")
                        # Update both tables
                        update_overtime_number(Session, game["gameId"])
                        update_alert_sent(Session, game["gameId"])
                elif self.isCluthTime(game):
                    logger.info(
                        f"Clutch Game detected: {awayTeam} v {homeTeam} - checking db"
                    )
                    if not check_alert_sent(Session, game["gameId"]):
                        insert_game(Session, game["gameId"])
                        logger.info(
                            f"Alerting for Clutch Game: {awayTeam} v {homeTeam}"
                        )
                        self.send_alert(game, "clutch")
                        update_alert_sent(Session, game["gameId"])

            # Sleep for 2 hours if there are no live games
            if len(games) == 0:
                logger.info("No live games. Sleeping for 2 hours...")
                clear_table(Session)
                time.sleep(7200)
            # Otherwise sleep for 30 seconds
            else:
                time.sleep(15)
