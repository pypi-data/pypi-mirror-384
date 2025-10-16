import pytest
from unittest.mock import patch, MagicMock
from clutchtimealerts.scraper.live_scores import NBAScoreScraper


@pytest.fixture
def mock_response():
    """Fixture for mock API response data."""
    return {
        "scoreboard": {
            "games": [
                {
                    "gameId": "001",
                    "gameStatus": 2,
                    "homeTeam": {
                        "teamTricode": "LAL",
                        "score": 95,
                    },
                    "awayTeam": {
                        "teamTricode": "GSW",
                        "score": 100,
                    },
                },
                {
                    "gameId": "002",
                    "gameStatus": 1,
                    "homeTeam": {
                        "teamTricode": "BOS",
                        "score": 0,
                    },
                    "awayTeam": {
                        "teamTricode": "MIA",
                        "score": 0,
                    },
                },
            ]
        }
    }


@patch("clutchtimealerts.scraper.live_scores.requests.get")
def test_load_json_success(mock_get, mock_response):
    """Test that load_json returns parsed JSON data on successful request."""
    mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)

    scraper = NBAScoreScraper()
    data = scraper.load_json()

    # Assertions
    mock_get.assert_called_once_with(scraper.url)
    assert data == mock_response


@patch("clutchtimealerts.scraper.live_scores.requests.get")
def test_load_json_failure(mock_get):
    """Test that load_json returns None on failed request."""
    mock_get.return_value = MagicMock(status_code=404)

    scraper = NBAScoreScraper()
    data = scraper.load_json()

    # Assertions
    mock_get.assert_called_once_with(scraper.url)
    assert data is None


@patch("clutchtimealerts.scraper.live_scores.requests.get")
def test_live_games(mock_get, mock_response):
    """Test that live_games returns only games with gameStatus == 2."""
    mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_response)

    scraper = NBAScoreScraper()
    live_games = scraper.live_games()

    # Assertions
    mock_get.assert_called_once_with(scraper.url)
    assert len(live_games) == 1
    assert live_games[0]["gameId"] == "001"
    assert live_games[0]["homeTeam"]["teamTricode"] == "LAL"
    assert live_games[0]["awayTeam"]["teamTricode"] == "GSW"


@patch("clutchtimealerts.scraper.live_scores.requests.get")
def test_live_games_no_live_data(mock_get):
    """Test that live_games returns an empty list if no live games are available."""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "scoreboard": {
                "games": [
                    {
                        "gameId": "003",
                        "gameStatus": 1,
                        "homeTeam": {
                            "teamTricode": "PHI",
                            "score": 0,
                        },
                        "awayTeam": {
                            "teamTricode": "NYK",
                            "score": 0,
                        },
                    }
                ]
            }
        },
    )

    scraper = NBAScoreScraper()
    live_games = scraper.live_games()

    # Assertions
    mock_get.assert_called_once_with(scraper.url)
    assert live_games == []
