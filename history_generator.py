# history_generator.py
import csv
import requests
import copy
from data_loader import load_teams_from_csv, save_teams_to_csv
from predict import predict_winner
from team import parse_game_json, Team

def generate_prediction_history():
    """
    Generates a CSV file containing NFL game predictions and results for both the
    regular season and postseason for the years 2022, 2023, and 2024.
    """
    fieldnames = [
        'year', 'seasontype', 'week', 'game_id', 'home_team', 'away_team', 
        'predicted_winner', 'actual_winner', 'home_win_prob', 'away_win_prob', 'is_correct'
    ]
    
    boxscore_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="

    with open('prediction_history.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        old_teams = load_teams_from_csv('nfl2021.csv')

        for year in range(2022, 2025):
            print(f"\n--- Processing Year: {year} ---")
            new_teams = load_teams_from_csv('nfl2021.csv')
            
            # Loop through both regular season (2) and postseason (3)
            for seasontype in [2, 3]:
                season_name = "Regular Season" if seasontype == 2 else "Postseason"
                week_range = range(1, 19) if seasontype == 2 else range(1, 6) # Postseason has up to 5 events (WC, DIV, CONF, PROBOWL, SB)
                
                print(f"  -- Processing {season_name} --")

                for week in week_range:
                    # Skip week 4 of the postseason (Pro Bowl)
                    if seasontype == 3 and week == 4:
                        print(f"    Skipping Postseason Week 4 (Pro Bowl).")
                        continue

                    prediction_week = week if seasontype == 2 else 18 + week

                    print(f"    Processing {year}, {season_name}, Week {week}...")
                    weekly_schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&seasontype={seasontype}&dates={year}&week={week}"
                    
                    try:
                        weekly_response = requests.get(weekly_schedule_url)
                        weekly_response.raise_for_status()
                        events = weekly_response.json().get('events', [])

                        if not events:
                            if seasontype == 3:
                                print(f"      No games found for Postseason Week {week}. Ending postseason processing.")
                                break 
                            continue

                        for game in events:
                            game_id = game.get('id')
                            competition = game['competitions'][0]
                            competitors = competition['competitors']
                            
                            home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                            away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})

                            if not home_team_data or not away_team_data: continue

                            home_team_abv = home_team_data.get('team', {}).get('abbreviation')
                            away_team_abv = away_team_data.get('team', {}).get('abbreviation')

                            predicted_winner, team1_prob, team2_prob = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams, prediction_week, home_team_abv)
                            
                            actual_winner, is_correct = None, None
                            if game.get('status', {}).get('type', {}).get('completed', False):
                                home_score = int(home_team_data.get('score', 0))
                                away_score = int(away_team_data.get('score', 0))
                                actual_winner = home_team_abv if home_score > away_score else away_team_abv
                                if predicted_winner and actual_winner:
                                    is_correct = (predicted_winner == actual_winner)

                            writer.writerow({
                                'year': year, 'seasontype': seasontype, 'week': week, 'game_id': game_id,
                                'home_team': home_team_abv, 'away_team': away_team_abv,
                                'predicted_winner': predicted_winner, 'actual_winner': actual_winner,
                                'home_win_prob': team1_prob, 'away_win_prob': team2_prob, 'is_correct': is_correct
                            })
                        
                        if seasontype == 2:
                            for game in events:
                                if game.get('status', {}).get('type', {}).get('completed', False):
                                    game_id = game.get('id')
                                    try:
                                        box_res = requests.get(f"{boxscore_base_url}{game_id}")
                                        box_res.raise_for_status()
                                        parse_game_json(box_res.json(), new_teams)
                                    except requests.RequestException as e:
                                        print(f"      Could not parse game {game_id} to update stats: {e}")

                    except requests.RequestException as e:
                        print(f"      Could not fetch data for Week {week}: {e}")
            
            old_teams = copy.deepcopy(new_teams)
        
        save_teams_to_csv(new_teams, 'final_team_stats.csv')
    print("\nPrediction history generation complete!")

if __name__ == '__main__':
    generate_prediction_history()