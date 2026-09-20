# riot-games-api

Personal CLI tool to inspect League of Legends match history and aggregate player stats directly in the terminal without opening bloated web trackers.

It talks to Riot's Account-v1 and Match-v5 endpoints, keeps match payloads in a local SQLite file to stay within the personal API rate limits (20 req/sec, 100 req/2 min), and calculates win rates, creep scores, vision scores, and kill participation.

## Requirements

Python 3.10+ and an active Riot developer API key from developer.riotgames.com.

```cmd
pip install -r requirements.txt
```

## Setup

Set your API key in the environment:

```cmd
set RIOT_API_KEY=RGAPI-xxxx-xxxx-xxxx
```

Or pass it via the `--key` flag.

## Usage

Show aggregate performance for recent games:

```cmd
python cli.py stats "Player#NA1" --region americas --count 20
```

Filter by queue type (420 = Ranked Solo/Duo, 440 = Ranked Flex, 450 = ARAM):

```cmd
python cli.py stats "Player#NA1" --region americas --queue 420
```

Inspect champ win rates and average CS per minute:

```cmd
python cli.py champs "Player#NA1" --region americas
```

Dump a raw match record directly from the local store or API:

```cmd
python cli.py inspect NA1_5123984123 --region americas
```

<!-- last-sync: 2026-09-20 -->
