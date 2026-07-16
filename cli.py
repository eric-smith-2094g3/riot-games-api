import argparse
import sys
from cli.riot_client import RiotClient
from cli.storage import (
    init_db,
    get_cached_account,
    save_account,
    get_cached_match,
    save_match,
)


QUEUE_NAMES = {
    420: "Ranked Solo",
    440: "Ranked Flex",
    400: "Normal Draft",
    430: "Normal Blind",
    450: "ARAM",
    1700: "Arena",
}


def parse_args():
    p = argparse.ArgumentParser(description="League match stats summary")
    p.add_argument("summoner", help="Riot ID formatted like Name#TAG")
    p.add_argument("--region", default="na1", help="Platform region, na1/euw1/etc")
    p.add_argument("-n", "--count", type=int, default=10, help="Matches to pull")
    p.add_argument("--ranked", action="store_true", help="Filter only ranked solo games")
    return p.parse_args()


def render_match_row(p, duration_min, queue_id):
    # TODO: pull surrender status from p['gameEndedInSurrender']
    result = "WIN" if p["win"] else "LOSS"
    champ = p.get("championName", "Unknown")
    k = p["kills"]
    d = p["deaths"]
    a = p["assists"]
    cs = p["totalMinionsKilled"] + p.get("neutralMinionsKilled", 0)
    cs_min = (cs / duration_min) if duration_min > 0 else 0.0
    dmg = p.get("totalDamageDealtToChampions", 0)
    q_name = QUEUE_NAMES.get(queue_id, f"Q:{queue_id}")

    kda_str = f"{k}/{d}/{a}"
    return (
        f"{result:<5} {champ:<14} {kda_str:<10} "
        f"{cs:>3} cs ({cs_min:.1f}/m)  "
        f"{dmg:>6} dmg  [{q_name}]"
    )


def run_summary():
    """Main runner for fetching, caching, and showing summary stats."""
    init_db()
    args = parse_args()

    if "#" not in args.summoner:
        print("error: Riot ID must be formatted as Name#TAG")
        sys.exit(1)

    name, tag = args.summoner.split("#", 1)
    name = name.strip()
    tag = tag.strip()

    client = RiotClient(region=args.region)

    puuid = get_cached_account(name, tag)
    if not puuid:
        acc = client.get_account_by_riot_id(name, tag)
        if not acc:
            print(f"error: could not locate account {name}#{tag}")
            sys.exit(1)
        puuid = acc["puuid"]
        save_account(name, tag, puuid)

    queue_arg = 420 if args.ranked else None
    match_ids = client.get_match_ids(puuid, count=args.count, queue=queue_arg)
    if not match_ids:
        print("no matches returned.")
        return

    print(f"Stats for {name}#{tag} ({args.region.upper()}) over last {len(match_ids)} games:")
    print("-" * 65)

    wins = 0
    total_kills = 0
    total_deaths = 0
    total_assists = 0
    total_damage = 0
    total_time = 0

    for mid in match_ids:
        payload = get_cached_match(mid)
        if not payload:
            payload = client.get_match(mid)
            if payload:
                save_match(mid, payload)
        if not payload:
            continue

        info = payload.get("info", {})
        duration = info.get("gameDuration", 0)
        # Riot match-v5 gameDuration is seconds, but older patches sometimes used milliseconds
        if duration > 10000:
            duration = int(duration / 1000)
        duration_min = duration / 60 if duration else 1.0
        queue_id = info.get("queueId", 0)

        participant = None
        for part in info.get("participants", []):
            if part.get("puuid") == puuid:
                participant = part
                break

        if not participant:
            continue

        if participant["win"]:
            wins += 1
        total_kills += participant["kills"]
        total_deaths += participant["deaths"]
        total_assists += participant["assists"]
        total_damage += participant.get("totalDamageDealtToChampions", 0)
        total_time += duration

        print(render_match_row(participant, duration_min, queue_id))

    count = len(match_ids)
    if count > 0:
        wr = (wins / count) * 100
        kda_ratio = (total_kills + total_assists) / max(1, total_deaths)
        avg_dmg = int(total_damage / count)
        print("-" * 65)
        print(
            f"Winrate: {wins}/{count} ({wr:.1f}%) | "
            f"KDA: {kda_ratio:.2f} ({total_kills}/{total_deaths}/{total_assists}) | "
            f"Avg Dmg: {avg_dmg}"
        )


def main():
    try:
        run_summary()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
