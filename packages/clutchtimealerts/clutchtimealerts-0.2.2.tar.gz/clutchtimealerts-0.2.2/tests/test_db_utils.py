import pytest
import sqlite3
from clutchtimealerts.db_utils import (
    TABLE_NAME,
    get_engine,
    check_and_recreate_table,
    clear_table,
    insert_game,
    update_alert_sent,
    check_alert_sent,
    check_overtime_alert_sent,
    update_overtime_number,
)
import tempfile


@pytest.fixture
def db_name():
    """Fixture to create a fresh instance of NotificationCollector."""
    temp_file = tempfile.NamedTemporaryFile()
    temp_file_name = temp_file.name
    return temp_file_name


def test_check_and_recreate_table(db_name):
    """Test that the table is created with the expected schema."""
    database_url = f"sqlite:///{db_name}"
    _, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()

    # Get the schema of the table
    cursor.execute(f"PRAGMA table_info({TABLE_NAME});")
    data = cursor.fetchall()
    connection.close()
    schema = []
    for row in data:
        row_name = row[1]
        row_type = row[2]
        not_null = " NOT NULL" if row[3] else ""
        default_value = f" DEFAULT {row[4]}" if row[4] else ""
        primary_key = " PRIMARY KEY" if row[5] else ""

        schema.append((row_name, f"{row_type}{not_null}{default_value}{primary_key}"))

    connection.close()


def test_insert_game(db_name):
    """Test inserting a new game."""
    database_url = f"sqlite:///{db_name}"
    Session, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    gameid = "0022400205"
    insert_game(Session, gameid)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT gameid FROM {TABLE_NAME} WHERE gameid = '{gameid}';")
    result = cursor.fetchone()
    connection.close()

    assert result is not None
    assert result[0] == gameid


def test_update_alert_sent(db_name):
    """Test updating the alert_sent column."""
    database_url = f"sqlite:///{db_name}"
    Session, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    # Check initial alerts is 0
    gameid = "0022400205"
    insert_game(Session, gameid)
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT alert_sent FROM {TABLE_NAME} WHERE gameid = '{gameid}';")
    result = cursor.fetchone()
    connection.close()

    assert result[0] == 0

    # Test updated alert
    update_alert_sent(Session, gameid)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT alert_sent FROM {TABLE_NAME} WHERE gameid = '{gameid}';")
    result = cursor.fetchone()
    connection.close()

    assert result[0] == 1


def test_check_alert_sent(db_name):
    """Test checking the alert_sent status."""
    database_url = f"sqlite:///{db_name}"
    Session, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    gameid = "0022400205"
    insert_game(Session, gameid)
    assert not check_alert_sent(Session, gameid)

    update_alert_sent(Session, gameid)
    assert check_alert_sent(Session, gameid)


def test_check_overtime_alert_sent(db_name):
    """Test checking the overtime_alert_number status."""
    database_url = f"sqlite:///{db_name}"
    Session, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    gameid = "0022400205"
    insert_game(Session, gameid)

    assert not check_overtime_alert_sent(Session, gameid, 1)

    update_overtime_number(Session, gameid)
    assert check_overtime_alert_sent(Session, gameid, 0)
    assert check_overtime_alert_sent(Session, gameid, 1)
    assert not check_overtime_alert_sent(Session, gameid, 2)

    update_overtime_number(Session, gameid)
    assert check_overtime_alert_sent(Session, gameid, 1)
    assert check_overtime_alert_sent(Session, gameid, 2)
    assert not check_overtime_alert_sent(Session, gameid, 3)


def test_update_overtime_number(db_name):
    """Test incrementing the overtime_alert_number."""
    database_url = f"sqlite:///{db_name}"
    Session, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    gameid = "0022400205"
    insert_game(Session, gameid)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT overtime_alert_number FROM {TABLE_NAME} WHERE gameid = '{gameid}';"
    )
    result = cursor.fetchone()
    connection.close()

    assert result[0] == 0

    update_overtime_number(Session, gameid)
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT overtime_alert_number FROM {TABLE_NAME} WHERE gameid = '{gameid}';"
    )
    result = cursor.fetchone()
    connection.close()

    assert result[0] == 1

    update_overtime_number(Session, gameid)
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT overtime_alert_number FROM {TABLE_NAME} WHERE gameid = '{gameid}';"
    )
    result = cursor.fetchone()
    connection.close()

    assert result[0] == 2


def test_clear_table(db_name):
    """Test clearing the table."""
    database_url = f"sqlite:///{db_name}"
    Session, engine = get_engine(database_url)
    check_and_recreate_table(engine=engine)

    gameid = "0022400205"
    insert_game(Session, gameid)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {TABLE_NAME};")
    result = cursor.fetchall()
    connection.close()

    assert len(result) == 1

    clear_table(Session)

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {TABLE_NAME};")
    result = cursor.fetchall()
    connection.close()

    assert len(result) == 0
