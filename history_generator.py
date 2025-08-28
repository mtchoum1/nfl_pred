# history_generator.py
import csv
import copy
from data_loader import load_teams_from_csv, save_teams_to_csv
from predict import predict_winner
from team import parse_game_json
import espn_api # Use the new centralized API module

def generate_prediction_history():
    fieldnames = [
        'year', 'seasontype', 'week', 'game_id', 'home_team', 'away_team', 
        'predicted_winner', 'actual_winner', 'home_win_prob', 'away_win_prob', 'is_correct'
    ]
    
    with open('prediction_history.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        old_teams = load_teams_from_csv('nfl2021.csv')

        for year in range(2022, 2025):
            print(f"\n--- Processing Year: {year} ---")
            new_teams = load_teams_from_csv('team_abv.csv')
            
            for seasontype in [2, 3]: # 2: Regular, 3: Postseason
                season_name = "Regular Season" if seasontype == 2 else "Postseason"
                week_range = range(1, 19) if seasontype == 2 else range(1, 6)
                
                print(f"  -- Processing {season_name} --")

                for week in week_range:
                    if seasontype == 3 and week == 4: # Skip Pro Bowl
                        continue

                    print(f"    Processing {year}, {season_name}, Week {week}...")
                    
                    weekly_data, error = espn_api.get_weekly_schedule(year, seasontype, week)
                    if error or not weekly_data or not weekly_data.get('events'):
                        if seasontype == 3: break # End postseason if no more games
                        continue

                    events = weekly_data['events']
                    
                    # Phase 1: Make predictions for all games in the week
                    for game in events:
                        game_id = game.get('id')
                        home_team_data, away_team_data = espn_api.parse_competitors(game)
                        if not home_team_data or not away_team_data: continue

                        home_team_abv = home_team_data.get('team', {}).get('abbreviation')
                        away_team_abv = away_team_data.get('team', {}).get('abbreviation')

                        prediction_week = week if seasontype == 2 else 18 + week
                        predicted_winner, home_prob, away_prob = predict_winner(
                            home_team_abv, away_team_abv, old_teams, new_teams, 
                            prediction_week, home_team_abv
                        )
                        
                        actual_winner, is_correct = None, None
                        if game.get('status', {}).get('type', {}).get('completed', False):
                            actual_winner = home_team_abv if home_team_data.get('winner') else (away_team_abv if away_team_data.get('winner') else None)
                            if predicted_winner and actual_winner:
                                is_correct = (predicted_winner == actual_winner)

                        writer.writerow({
                            'year': year, 'seasontype': seasontype, 'week': week, 'game_id': game_id,
                            'home_team': home_team_abv, 'away_team': away_team_abv,
                            'predicted_winner': predicted_winner, 'actual_winner': actual_winner,
                            'home_win_prob': home_prob, 'away_win_prob': away_prob, 'is_correct': is_correct
                        })
                    
                    # Phase 2: Update team stats from completed games
                    for game in events:
                        if game.get('status', {}).get('type', {}).get('completed', False):
                            game_id = game.get('id')
                            box_data, box_error = espn_api.get_boxscore(game_id)
                            if box_error:
                                print(f"      Could not get boxscore for {game_id}: {box_error}")
                                continue
                            parse_game_json(box_data, new_teams)
            
            old_teams = copy.deepcopy(new_teams)
        
        save_teams_to_csv(new_teams, 'final_team_stats.csv')
    print("\nPrediction history generation complete!")

if __name__ == '__main__':
    generate_prediction_history()