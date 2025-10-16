# ClutchTimeAlerts - NBA Clutch Time Alert Service

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/clutchtimealerts.svg)](https://badge.fury.io/py/clutchtimealerts)

A service that tracks ongoing NBA games and sends alerts when games enter "clutch time"—the last five minutes of the fourth quarter or overtime when the point difference is five points or fewer. The serivce monitors live game data and sends notifications via configured messaging platforms (such as GroupMe, Slack, etc.) to keep you informed of the most intense moments.

# Features
- **Real-Time Clutch Detection**: Monitors live NBA game data and detects when games enter clutch time.
- **Customizable Alerts**: Configure the service to send alerts on various platforms (GroupMe, Slack, etc.).
- **Multiple Game Support**: Tracks multiple NBA games simultaneously to ensure you don't miss any clutch moments.

# Supported Notification Types

We currently support the following notification types out of the box:

- **GroupMe** 
- **Slack**
- **Ntfy**
- **Twilio** (SMS)

On our road map we want to expand the supported notification types. If there's a type you want to see supported add an issue or submit a PR for review.

# Installation 

There are two different supported installation types: Python and Docker.

**Python**

To install the python package you can install it from [PYPI](https://pypi.org/project/clutchtimealerts/)

```sh
pip install clutchtimealerts
```

Alertnatively you can clone the repository then install it directly.
 
```sh
git clone git@github.com:bwalheim1205/clutchtimealerts.git
cd clutchtimealerts
pip install clutchtimealerts
```

**Docker**

To install via docker, you can pull image from [Docker Hub](https://hub.docker.com/repository/docker/bwalheim1205/clutchtimealerts):

```sh
docker pull bwalheim1205/clutchtimealerts
```


Alertnatively you can build the image from source:


```sh
git clone git@github.com:bwalheim1205/clutchtimealerts.git
docker build clutchtimealerts/ -t clutchtimealerts
```

# Usage

## Configuration File

The alert system utilizes a yaml configuration file. YAML contains configuration 
options for SQLite database and alert method configurations. Here is an example
of a configuration file

**Example Configuration**

```yaml
db_url: clutchtime.db

notifications:
  - type: GroupMe
    config:
      bot_id: "<group-bot-id>"
  - type: Slack
    nba_teams:
        - PHI
        - MIL
    config:
      channel: "#general"
      token: "<slack-api-token>"
  - type: Twilio
    config:
      account_sid: "<twilio-accout-sid>"
      auth_token: "<twilio-auth-token>"
      from: "+14155551212"
      to: 
        - "+14155551212"
        - "+14155551212"
  - type: Ntfy
    config:
      host: <ntfy host>
      topic: nba_alerts
      token: <Ntfy auth token>
```

### YAML Fields

**db_url** (__Optional__): DB url to sqlite3 database. Defaults to sqlite:///clutchtime.db

**notification_format** (__Optional__): fstring for formatting clutch alert message. Defaults to "Clutch Game\n{HOME_TEAM_TRI} {HOME_TEAM_SCORE} - {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}\n{NBA_COM_STREAM}"

**ot_format** (__Optional__): fstring for formatting ot alert messages. Defaults to "OT{OT_NUMBER} Alert\n{HOME_TEAM_TRI} {HOME_TEAM_SCORE} - {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}\n{NBA_COM_STREAM}"

**nba_teams** (__Optional__): a list of NBA team tricodes that you wish to receive notifications list. Defaluts to all NBA teams

**notifications**: List of notification configs
-  **type**: class name or common name of the alert type
-  **notification_format** (__Optional__): fstring for formatting clutch alert messages overwrites global level config.
-  **ot_format** (__Optional__): fstring for formatting ot alert messages. Overwrites global level config
-  **nba_teams** (__Optional__): a list of NBA team tricodes that you wish to receive notifications list. Overwrites global level config
-  **config**: kwargs** for the alert classes

### Format Langauge

To create a format message we use python fstring format. Below is an example

Example:

```python
"Clutch Game\n{HOME_TEAM_TRI} {HOME_TEAM_SCORE} - {AWAY_TEAM_SCORE} {AWAY_TEAM_TRI}\n{NBA_COM_STREAM}"
```

Here's a list of valid values that can be used in fstring:

- **HOME_TEAM_TRI**: Tricode for home team. Ex: PHI
- **HOME_TEAM_CITY**: City for home team. Ex: Philadelphia
- **HOME_TEAM_NAME**: Team name for home team. Ex: 76ers
- **HOME_TEAM_WINS**: Total wins for home team this season
- **HOME_TEAM_LOSSES**: Total losses for home team this season
- **HOME_TEAM_SCORE**: Home teams score this game
- **AWAY_TEAM_TRI**: Tricode for away team. Ex: BOS
- **AWAY_TEAM_CITY**: City for away team. Ex: Boston
- **AWAY_TEAM_NAME**: Team name for away team. Ex: Celtics
- **AWAY_TEAM_WINS**: Total wins for away team this season
- **AWAY_TEAM_LOSSES**: Total losses for away team this season
- **AWAY_TEAM_SCORE**: Away teams score this game
- **GAME_ID**: Id for the hame. Ex: 0022400580
- **GAME_CLOCK**: Game Clock string. Ex: PT06M01.00S
- **GAME_STATUS_TEXT**: String for game status. Ex:  "Q3 6:01"
- **OT_NUMBER**: Number for OT Period
- **NBA_COM_STREAM**: Link to watch game on nba.com


## Running Alert Service

Once you've generated a configuration file you can run alert service
using one of the following commands

**Python**

```sh
python3 -m clutchtimealerts -f <path-to-config>
```

**Docker**
```sh
docker run -v <path-to-config>:/app/config.yml clutchtimealerts
```