# cron_jobs.py
import sys
from firebase_admin import db
from firebase_config import initialize_firebase
import espn_api

# Initialize Firebase connection
initialize_firebase()

def get_weekly_winners(year, week):
    """Fetches game results and returns a set of winning team abbreviations."""
    print(f"Fetching game winners for {year}, Week {week}...")
    data, error = espn_api.get_weekly_schedule(year, 2, week) # LMS is always regular season
    if error:
        print(f"Error fetching game data: {error}")
        return None

    winners = set()
    for game in data.get('events', []):
        if game.get('status', {}).get('type', {}).get('name') == 'STATUS_FINAL':
            home_team, away_team = espn_api.parse_competitors(game)
            # The 'winner' flag can be on either competitor object
            if home_team.get('winner'):
                winners.add(home_team['team']['abbreviation'])
            elif away_team.get('winner'):
                winners.add(away_team['team']['abbreviation'])
    return winners

def process_lms_week(year, week):
    """Checks each player's pick and updates its result in the database."""
    print(f"--- Processing Last Man Standing for {year}, Week {week} ---")
    winning_teams = get_weekly_winners(year, week)
    if winning_teams is None:
        print("Could not retrieve winning teams. Aborting.")
        return

    lms_ref = db.reference(f'last_man_standing/{year}')
    all_players = lms_ref.get()
    if not all_players:
        print("No players found for this year.")
        return

    for user_id, player_data in all_players.items():
        if not isinstance(player_data, dict): continue

        pick_data = player_data.get('picks', {}).get(str(week))
        
        # Skip if no pick, or if already processed
        if not pick_data or (isinstance(pick_data, dict) and pick_data.get('result') != 'unknown'):
            continue
        
        # Handle both old (string) and new (object) data formats
        team_picked = pick_data if isinstance(pick_data, str) else pick_data.get('team')
        if not team_picked:
            continue

        is_correct = team_picked in winning_teams
        result = "correct" if is_correct else "incorrect"

        db.reference(f'last_man_standing/{year}/{user_id}/picks/{week}').set({
            "team": team_picked, 
            "result": result
        })
        
        if not is_correct:
            db.reference(f'last_man_standing/{year}/{user_id}/status').set('eliminated')
        
        print(f"User {user_id} pick '{team_picked}' for week {week} was {result}.")

    print(f"--- Processing complete for Week {week}. ---")

if __name__ == '__main__':
    if len(sys.argv) == 3:
        try:
            year = int(sys.argv[1])
            week_to_process = int(sys.argv[2])
            process_lms_week(year, week_to_process)
        except ValueError:
            print("Year and week must be integers.")
    else:
        print("Usage: python cron_jobs.py <year> <week_to_process>")