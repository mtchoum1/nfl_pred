# history_generator.py
import csv
import requests
import copy
from data_loader import load_teams_from_csv
from predict import predict_winner
from team import parse_game_json, Team

def generate_prediction_history():
    """
    Generates a CSV file containing NFL game predictions and results
    for the years 2022, 2023, and 2024. For each year, the "old_teams" data
    is based on the stats from the previously completed season.
    """
    fieldnames = [
        'year', 'week', 'game_id', 'home_team', 'away_team', 
        'predicted_winner', 'actual_winner', 'home_win_prob', 'away_win_prob', 'is_correct'
    ]
    
    boxscore_base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event="

    with open('prediction_history.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Initialize old_teams. For the first year (2022), it will be a blank slate.
        old_teams = load_teams_from_csv('team_abv.csv')

        for year in range(2022, 2025):
            print(f"\n--- Processing Year: {year} ---")
            # 'new_teams' holds the accumulating stats for the current year. Reset it each year.
            new_teams = load_teams_from_csv('team_abv.csv')
            
            # For predictions in the current year, 'old_teams' should have the stats
            # from the *end* of the previous year.
            print(f"Using {year-1} final stats as historical data for {year} predictions.")

            for week in range(1, 19): # 18 weeks
                print(f"  Processing {year}, Week {week}...")
                weekly_schedule_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}&week={week}"
                
                try:
                    weekly_response = requests.get(weekly_schedule_url)
                    weekly_response.raise_for_status()
                    events = weekly_response.json().get('events', [])

                    if not events:
                        print(f"    No games found for Week {week}. Moving to next week.")
                        continue

                    # First, predict all games of the week based on stats *before* this week's games
                    games_to_process = []
                    for game in events:
                        game_id = game.get('id')
                        competition = game['competitions'][0]
                        competitors = competition['competitors']
                        
                        home_team_data = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                        away_team_data = next((c for c in competitors if c.get('homeAway') == 'away'), {})

                        if not home_team_data or not away_team_data:
                            continue

                        home_team_abv = home_team_data.get('team', {}).get('abbreviation')
                        away_team_abv = away_team_data.get('team', {}).get('abbreviation')

                        predicted_winner, team1_prob, team2_prob = predict_winner(home_team_abv, away_team_abv, old_teams, new_teams)
                        
                        home_prob = team1_prob
                        away_prob = team2_prob

                        actual_winner = None
                        is_correct = None
                        if game.get('status', {}).get('type', {}).get('completed', False):
                            home_score = int(home_team_data.get('score', 0))
                            away_score = int(away_team_data.get('score', 0))
                            if home_score > away_score:
                                actual_winner = home_team_abv
                            elif away_score > home_score:
                                actual_winner = away_team_abv
                            elif home_score == away_score:
                                actual_winner = predicted_winner
                            
                            if predicted_winner and actual_winner:
                                is_correct = (predicted_winner == actual_winner)

                        writer.writerow({
                            'year': year,
                            'week': week,
                            'game_id': game_id,
                            'home_team': home_team_abv,
                            'away_team': away_team_abv,
                            'predicted_winner': predicted_winner,
                            'actual_winner': actual_winner,
                            'home_win_prob': home_prob,
                            'away_win_prob': away_prob,
                            'is_correct': is_correct
                        })
                    
                    # After the week's predictions are saved, update the 'new_teams' stats with the actual results
                    for game in events:
                         if game.get('status', {}).get('type', {}).get('completed', False):
                            game_id = game.get('id')
                            try:
                                box_res = requests.get(f"{boxscore_base_url}{game_id}")
                                box_res.raise_for_status()
                                parse_game_json(box_res.json(), new_teams)
                            except requests.RequestException as e:
                                print(f"    Could not parse game {game_id} to update stats: {e}")


                except requests.RequestException as e:
                    print(f"    Could not fetch data for Week {week}: {e}")
            
            # After the entire year is processed, the final 'new_teams' stats
            # become the 'old_teams' for the next year's loop.
            old_teams = copy.deepcopy(new_teams)


    print("\nPrediction history generation complete! File saved as 'prediction_history.csv'")

if __name__ == '__main__':
    generate_prediction_history()