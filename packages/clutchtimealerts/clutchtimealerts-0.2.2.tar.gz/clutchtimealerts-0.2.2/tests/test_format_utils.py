import pytest
from clutchtimealerts.format_utils import format_message


@pytest.fixture
def game_data():
    return {
        "gameId": "0022400580",
        "gameCode": "20250117/TORMIL",
        "gameStatus": 2,
        "gameStatusText": "Q3 6:01",
        "period": 3,
        "gameClock": "PT06M01.00S",
        "gameTimeUTC": "2025-01-18T01:00:00Z",
        "gameEt": "2025-01-17T20:00:00-05:00",
        "regulationPeriods": 4,
        "ifNecessary": False,
        "seriesGameNumber": "",
        "gameLabel": "",
        "gameSubLabel": "",
        "seriesText": "",
        "seriesConference": "",
        "poRoundDesc": "",
        "gameSubtype": "",
        "isNeutral": False,
        "homeTeam": {
            "teamId": 1610612749,
            "teamName": "Bucks",
            "teamCity": "Milwaukee",
            "teamTricode": "MIL",
            "wins": 22,
            "losses": 17,
            "score": 90,
            "seed": None,
            "inBonus": "0",
            "timeoutsRemaining": 5,
            "periods": [
                {"period": 1, "periodType": "REGULAR", "score": 37},
                {"period": 2, "periodType": "REGULAR", "score": 35},
                {"period": 3, "periodType": "REGULAR", "score": 18},
                {"period": 4, "periodType": "REGULAR", "score": 0},
            ],
        },
        "awayTeam": {
            "teamId": 1610612761,
            "teamName": "Raptors",
            "teamCity": "Toronto",
            "teamTricode": "TOR",
            "wins": 10,
            "losses": 31,
            "score": 78,
            "seed": None,
            "inBonus": "0",
            "timeoutsRemaining": 4,
            "periods": [
                {"period": 1, "periodType": "REGULAR", "score": 22},
                {"period": 2, "periodType": "REGULAR", "score": 35},
                {"period": 3, "periodType": "REGULAR", "score": 21},
                {"period": 4, "periodType": "REGULAR", "score": 0},
            ],
        },
    }


def test_format_message(game_data):
    gameId = game_data["gameId"]
    homeTeam = game_data["homeTeam"]["teamTricode"]
    awayTeam = game_data["awayTeam"]["teamTricode"]
    game_data["nbaComStream"] = (
        f"https://www.nba.com/game/{awayTeam}-vs-{homeTeam}-{gameId}?watchLive=true"
    )
    fstring = "{HOME_TEAM_TRI} {HOME_TEAM_SCORE} {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}"
    expected_output = "MIL 90 78 TOR"
    actual_output = format_message(game_data, fstring)
    assert actual_output == expected_output

    fstring = "{NBA_COM_STREAM}"
    expected_output = "https://www.nba.com/game/TOR-vs-MIL-0022400580?watchLive=true"
    actual_output = format_message(game_data, fstring)
    assert actual_output == expected_output

    fstring = "{HOME_TEAM_CITY} {HOME_TEAM_NAME} {AWAY_TEAM_CITY} {AWAY_TEAM_NAME}"
    expected_output = "Milwaukee Bucks Toronto Raptors"
    actual_output = format_message(game_data, fstring)
    assert actual_output == expected_output

    fstring = "{HOME_TEAM_WINS} {HOME_TEAM_LOSSES} {AWAY_TEAM_WINS} {AWAY_TEAM_LOSSES}"
    expected_output = "22 17 10 31"
    actual_output = format_message(game_data, fstring)
    assert actual_output == expected_output

    fstring = "{GAME_ID} {GAME_STATUS_TEXT} {GAME_CLOCK}"
    expected_output = "0022400580 Q3 6:01 PT06M01.00S"
    actual_output = format_message(game_data, fstring)
    assert actual_output == expected_output


def test_format_message_ot(game_data):
    game_data["period"] = 5
    gameId = game_data["gameId"]
    homeTeam = game_data["homeTeam"]["teamTricode"]
    awayTeam = game_data["awayTeam"]["teamTricode"]
    game_data["nbaComStream"] = (
        f"https://www.nba.com/game/{awayTeam}-vs-{homeTeam}-{gameId}?watchLive=true"
    )

    fstring = "OT{OT_NUMBER} Alert\n{HOME_TEAM_TRI} {HOME_TEAM_SCORE} - {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}"
    expected_output = "OT1 Alert\nMIL 90 - 78 TOR"
    actual_output = format_message(game_data, fstring)
    assert actual_output == expected_output


def test_format_stream_bad_value(game_data):
    fstring = "{FAKE_VALUE}"
    try:
        format_message(game_data, fstring)
        assert False
    except KeyError:
        assert True
