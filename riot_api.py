# riot_api.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Load .env file

API_KEY = os.getenv("RIOT_API_KEY")

# Both the Riot Account endpoint and the Match V5 endpoint are on "americas" for NA.
ACCOUNT_REGION = "americas"
MATCH_REGION = "americas"

def get_puuid_by_riot_id(riot_id: str) -> str:
    """
    riot_id is expected to be in the format "Name#Tag".
    e.g., "TFBlade#122".
    This calls the Riot Account V1 endpoint to get the PUUID.
    """
    if "#" not in riot_id:
        raise ValueError("Riot ID must include '#' (e.g., 'TFBlade#122').")

    gameName, tagLine = riot_id.split("#", 1)

    url = f"https://{ACCOUNT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    headers = {"X-Riot-Token": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching PUUID: {response.text}")

    data = response.json()
    return data["puuid"]  # "puuid" in the response JSON

def get_match_ids(puuid: str, count: int = 10) -> list:
    """
    Uses Match V5 to get a list of match IDs for the given PUUID.
    Adjust 'count' to fetch the desired number of recent matches.
    """
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {"X-Riot-Token": API_KEY}
    params = {
        "start": 0,
        "count": count
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching match IDs: {response.text}")

    return response.json()

def get_match_data(match_id: str) -> dict:
    """
    Fetches detailed info about a single match using Match V5.
    """
    url = f"https://{MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching match data for {match_id}: {response.text}")

    return response.json()

def calculate_stats(riot_id: str, match_count: int = 10):
    """
    1. Convert "Name#Tag" (Riot ID) into a PUUID using Riot Account V1.
    2. Fetch the last `match_count` match IDs for that PUUID.
    3. Determine:
        - Overall Win rate (wins / total_matches)
        - Overall Average KDA
        - Per-champion stats (games, wins, losses, KDA, win rate)
    4. Return the overall stats + champion-level stats.
    """
    # 1. Get PUUID from the Riot ID
    puuid = get_puuid_by_riot_id(riot_id)

    # 2. Fetch match IDs
    match_ids = get_match_ids(puuid, match_count)
    total_matches = len(match_ids)

    # Track overall stats
    wins = 0
    total_kills = 0
    total_deaths = 0
    total_assists = 0

    # Track champion-level stats in a dict
    # Example structure:
    # champion_stats = {
    #   "Jax": {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0},
    #   ...
    # }
    champion_stats = {}

    # 3. Process each match
    for match_id in match_ids:
        match_data = get_match_data(match_id)
        participants = match_data["info"]["participants"]

        # Find the participant for our PUUID
        for participant in participants:
            if participant["puuid"] == puuid:
                # Overall stats
                if participant["win"]:
                    wins += 1
                total_kills += participant["kills"]
                total_deaths += participant["deaths"]
                total_assists += participant["assists"]

                # Champion-level stats
                champ_name = participant["championName"]
                if champ_name not in champion_stats:
                    champion_stats[champ_name] = {
                        "games": 0,
                        "wins": 0,
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0
                    }

                champion_stats[champ_name]["games"] += 1
                champion_stats[champ_name]["kills"] += participant["kills"]
                champion_stats[champ_name]["deaths"] += participant["deaths"]
                champion_stats[champ_name]["assists"] += participant["assists"]
                if participant["win"]:
                    champion_stats[champ_name]["wins"] += 1

                break  # Stop searching participants once we found our PUUID

    # Compute Overall Win Rate
    if total_matches > 0:
        overall_winrate = (wins / total_matches) * 100
    else:
        overall_winrate = 0.0

    # Compute Overall Average KDA
    overall_kda = (total_kills + total_assists) / max(1, total_deaths)

    # Build a list of champion stats to sort by "games" desc
    champion_stats_list = []
    for champ, stats in champion_stats.items():
        ch_games = stats["games"]
        ch_wins = stats["wins"]
        ch_losses = ch_games - ch_wins
        ch_winrate = (ch_wins / ch_games) * 100 if ch_games > 0 else 0
        ch_kda = (stats["kills"] + stats["assists"]) / max(1, stats["deaths"])
        champion_stats_list.append({
            "champion": champ,
            "games": ch_games,
            "wins": ch_wins,
            "losses": ch_losses,
            "winrate": ch_winrate,
            "kda": ch_kda
        })

    # Sort by number of games played, descending
    champion_stats_list.sort(key=lambda x: x["games"], reverse=True)

    # Return everything
    # We'll let main.py handle how to display the top 3, etc.
    return {
        "overall_winrate": overall_winrate,
        "total_matches": total_matches,
        "overall_kda": overall_kda,
        "champion_stats": champion_stats_list
    }
