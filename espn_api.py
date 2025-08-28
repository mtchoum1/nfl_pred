# espn_api.py
import requests

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

def _fetch_json(url):
    """
    Generic helper to fetch and parse JSON from a URL, with error handling.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as e:
        print(f"Could not fetch data from {url}: {e}")
        return None, str(e)

def get_weekly_schedule(year, seasontype, week):
    """
    Fetches the full schedule for a given week from the ESPN API.
    """
    url = f"{BASE_URL}/scoreboard?limit=1000&seasontype={seasontype}&dates={year}&week={week}"
    return _fetch_json(url)

def get_boxscore(game_id):
    """
    Fetches the boxscore/summary for a specific game ID.
    """
    url = f"{BASE_URL}/summary?event={game_id}"
    return _fetch_json(url)

def get_all_teams_data():
    """
    Fetches data for all NFL teams, typically used for logos and full names.
    """
    url = f"{BASE_URL}/teams"
    return _fetch_json(url)

def parse_competitors(game_event):
    """
    Parses a game event to extract home and away team data objects.
    Returns (home_team_data, away_team_data).
    """
    try:
        competition = game_event['competitions'][0]
        competitors = competition['competitors']
        home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
        away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})
        return home_team_data, away_team_data
    except (KeyError, IndexError, StopIteration):
        return {}, {}