from sqlalchemy import (
    create_engine,
    inspect,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
import datetime
import logging

logger = logging.getLogger("clutchtimealerts")

TABLE_NAME = "clutchgames"


class Base(DeclarativeBase):
    pass


class ClutchGame(Base):
    __tablename__ = TABLE_NAME

    id = Column(Integer, primary_key=True)
    gameid = Column(String, nullable=False)
    alert_time = Column(
        DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc)
    )
    alert_sent = Column(Boolean, nullable=False, default=False)
    overtime_alert_number = Column(Integer, nullable=False, default=0)


def get_engine(db_url: str):
    """
    Return a sqlalchemy Engine and Session factory based on the provided database url.

    Parameters
    ----------
    db_url : str
        The database url to use.

    Returns
    -------
    tuple[Session, Engine]
        A sqlalchemy Session factory and Engine instance.
    """
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session, engine


def check_and_recreate_table(engine):
    """
    Check if the ClutchGame table exists in the database, and if not, create it.
    If the table does exist, compare the current schema with the expected schema.
    If the schemas differ, drop the table and recreate it.

    Parameters
    ----------
    engine : Engine
        The sqlalchemy Engine instance to use.
    """
    inspector = inspect(engine)

    # Check if the table exists
    if not inspector.has_table(ClutchGame.__tablename__):
        logger.info("Table 'clutchgames' does not exist. Creating the table...")
        Base.metadata.create_all(engine)
        return

    # Compare the schemas
    current_columns = {
        column["name"]: column["type"]
        for column in inspector.get_columns(ClutchGame.__tablename__)
    }
    expected_columns = {
        column.name: column.type for column in ClutchGame.__table__.columns
    }
    if current_columns != expected_columns:
        logger.warning("Schema mismatch detected. Dropping the 'clutchgames' table...")
        ClutchGame.__table__.drop(engine)
        Base.metadata.create_all(engine)
        logger.debug("Table dropped and recreated.")

    try:
        Base.metadata.create_all(engine)
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")


def clear_table(Session):
    """
    Clear all records from the ClutchGame table in the database.

    Parameters
    ----------
    Session : sqlalchemy.orm.session.Session
        The sqlalchemy Session factory to use.

    Returns
    -------
    None
    """

    session = Session()
    try:
        session.query(ClutchGame).delete()
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error clearing table: {e}")
    finally:
        session.close()


def insert_game(Session, gameid: str):
    """
    Insert a new game into the database.

    Parameters
    ----------
    Session : sqlalchemy.orm.session.Session
        The sqlalchemy Session factory to use.
    gameid : str
        The game ID to insert.

    Returns
    -------
    None
    """
    session = Session()
    try:
        new_game = ClutchGame(gameid=gameid)
        session.add(new_game)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error inserting game: {e}")
    finally:
        session.close()


def update_alert_sent(Session, gameid: str):
    """
    Update the alert_sent status for a given game in the database.

    Parameters
    ----------
    Session : sqlalchemy.orm.session.Session
        The sqlalchemy Session factory to use.
    gameid : str
        The unique identifier of the game for which the alert_sent status should be updated.

    Returns
    -------
    None
    """

    session = Session()
    try:
        game = session.query(ClutchGame).filter_by(gameid=gameid).first()
        if game:
            game.alert_sent = True
            session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating alert_sent: {e}")
    finally:
        session.close()


def check_alert_sent(Session, gameid: str) -> bool:
    """
    Check if the alert_sent status for a given game in the database is True.

    Parameters
    ----------
    Session : sqlalchemy.orm.session.Session
        The sqlalchemy Session factory to use.
    gameid : str
        The unique identifier of the game for which the alert_sent status should be checked.

    Returns
    -------
    bool
        The alert_sent status of the given game in the database.
    """

    session = Session()
    try:
        game = session.query(ClutchGame).filter_by(gameid=gameid).first()
        return game.alert_sent if game else False
    except SQLAlchemyError as e:
        logger.error(f"Error checking alert_sent: {e}")
        return False
    finally:
        session.close()


def check_overtime_alert_sent(Session, gameid: str, overtime_number: int) -> bool:
    """
    Check if the overtime_alert_number for a given game in the database is equal to the given overtime_number.

    Parameters
    ----------
    Session : sqlalchemy.orm.session.Session
        The sqlalchemy Session factory to use.
    gameid : str
        The unique identifier of the game for which the alert_sent status should be checked.
    overtime_number : int
        The overtime alert number to check against.

    Returns
    -------
    bool
        True if the overtime_alert_number is equal to the given overtime_number, otherwise False.
    """
    session = Session()
    try:
        game = (
            session.query(ClutchGame)
            .filter(
                (ClutchGame.gameid == gameid)
                & (ClutchGame.overtime_alert_number >= overtime_number)
            )
            .first()
        )
        return game is not None
    except SQLAlchemyError as e:
        logger.error(f"Error checking overtime alert: {e}")
        return False
    finally:
        session.close()


def update_overtime_number(Session, gameid: str):
    """
    Increment the overtime_alert_number for a given game in the database.

    Parameters
    ----------
    Session : sqlalchemy.orm.session.Session
        The sqlalchemy Session factory to use.
    gameid : str
        The unique identifier of the game for which the overtime_alert_number should be incremented.

    Returns
    -------
    None
    """
    session = Session()
    try:
        game = session.query(ClutchGame).filter_by(gameid=gameid).first()
        if game:
            game.overtime_alert_number += 1
            session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating overtime number: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    DATABASE_URL = "sqlite:///example.db"
    Session, engine = get_engine(DATABASE_URL)

    # Ensure the table exists
    check_and_recreate_table(engine)

    # Example operations
    insert_game(Session, "game123")
    print(check_alert_sent(Session, "game123"))
    update_alert_sent(Session, "game123")
    print(check_alert_sent(Session, "game123"))
