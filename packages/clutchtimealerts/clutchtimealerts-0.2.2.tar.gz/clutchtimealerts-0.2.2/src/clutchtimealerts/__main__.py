from clutchtimealerts.clutch_alerts import ClutchAlertsService
from clutchtimealerts.config_parser import ConfigParser
from clutchtimealerts.notification_collector import NotificationCollector

import argparse
import logging
import os

logger = logging.getLogger("clutchtimealerts")

if __name__ == "__main__":
    # Parse Arguments
    parser = argparse.ArgumentParser(description="Choose a notification type.")
    parser.add_argument(
        "-f" "--file",
        dest="file",
        default="config.yml",
        type=str,
        required=False,
        help="Path to the YAML config file",
    )
    parser.add_argument(
        "-l",
        "--level",
        dest="level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str,
        required=False,
        help="Logging level",
    )
    args = parser.parse_args()

    # Set log level
    logger.setLevel(args.level)

    # Collect Notification Classes
    collector = NotificationCollector()
    notifcation_dir = os.path.dirname(__file__) + "/notifications"
    collector.collect_notifications(notifcation_dir)

    # Parse Config
    parser = ConfigParser(
        args.file, collector.classname_dict, collector.common_name_dict
    )
    parser.parse_config()

    alert_service = ClutchAlertsService(
        notification_configs=parser.notification_configs,
        db_url=parser.db_url,
    )
    alert_service.run()
