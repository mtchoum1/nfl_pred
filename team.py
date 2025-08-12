from math import pow

class Team:
    """
    Represents an NFL team's average statistics for various categories.
    """
    def __init__(self, pyds_for=0, pyds_agst=0, ryds_for=0, ryds_agst=0, takeaways=0, giveaways=0, points_for=0, points_agst=0, games=0):
        valid_games = max(games, 1)
        self.pyds_for = pyds_for
        self.pyds_agst = pyds_agst
        self.ryds_for = ryds_for
        self.ryds_agst = ryds_agst
        self.takeaways = takeaways
        self.giveaways = giveaways
        self.points_for = points_for
        self.points_agst = points_agst
        self.games = games

        self.avg_pyds_for = pyds_for / valid_games
        self.avg_pyds_agst = pyds_agst / valid_games
        self.avg_ryds_for = ryds_for / valid_games
        self.avg_ryds_agst = ryds_agst / valid_games
        self.avg_takeaways = takeaways / valid_games
        self.avg_giveaways = giveaways / valid_games
        self.avg_points_for = points_for / valid_games
        self.avg_points_agst = points_agst / valid_games

    def update_stats(self, pyds_for, pyds_agst, ryds_for, ryds_agst, takeaways, giveaways, points_for, points_agst):
        self.pyds_for += pyds_for
        self.pyds_agst += pyds_agst
        self.ryds_for += ryds_for
        self.ryds_agst += ryds_agst
        self.takeaways += takeaways
        self.giveaways += giveaways
        self.points_for += points_for
        self.points_agst += points_agst
        self.games += 1

        # Recalculate averages
        valid_games = max(self.games, 1)
        self.avg_pyds_for = self.pyds_for / valid_games
        self.avg_pyds_agst = self.pyds_agst / valid_games
        self.avg_ryds_for = self.ryds_for / valid_games
        self.avg_ryds_agst = self.ryds_agst / valid_games
        self.avg_takeaways = self.takeaways / valid_games
        self.avg_giveaways = self.giveaways / valid_games
        self.avg_points_for = self.points_for / valid_games
        self.avg_points_agst = self.points_agst / valid_games
    
    def __repr__(self):
        return (
            f"Team(games={self.games}, avg_pyds_for={self.avg_pyds_for:.2f}, avg_pyds_agst={self.avg_pyds_agst:.2f}, "
            f"avg_ryds_for={self.avg_ryds_for:.2f}, avg_ryds_agst={self.avg_ryds_agst:.2f}, "
            f"avg_takeaways={self.avg_takeaways:.2f}, avg_giveaways={self.avg_giveaways:.2f}, "
            f"avg_points_for={self.avg_points_for:.2f}, avg_points_agst={self.avg_points_agst:.2f})"
        )

def pyth_win(stat_for, stat_agst):
    denominator = pow(stat_for, 2.37) + pow(stat_agst, 2.37)
    if denominator == 0:
        return 0.5
    return pow(stat_for, 2.37) / denominator

def expect_stat(stat_for, stat_agst):
    return (stat_for + stat_agst) / 2

def get_weighted_stat(old_stat, new_stat, old_weight=0.2, new_weight=0.8):
    return (old_stat * old_weight) + (new_stat * new_weight)

def parse_game_json(game_data, team_objects):
    """
    Parses NFL game data from a JSON object structure and updates the associated Team objects.

    Args:
        game_data (dict): A dictionary containing game statistics.
        team_objects (dict): A dictionary mapping team abbreviations to Team objects.
    """
    try:
        # Navigate to the correct part of the JSON structure
        boxscore_data = game_data.get('boxscore', {})
        teams_data = boxscore_data.get('teams', [])
        
        # Get team abbreviations from the header
        header = game_data.get('header', {})
        competitions = header.get('competitions', [])
        if not competitions:
            print("Error: No competitions found in game data.")
            return

        competitors = competitions[0].get('competitors', [])
        if len(competitors) < 2:
            print(f"Error: Not enough competitors found for game {header.get('id')}.")
            return

        # Identify home and away teams based on the 'homeAway' key
        home_competitor_data = next((c for c in competitors if c.get('homeAway') == 'home'), None)
        away_competitor_data = next((c for c in competitors if c.get('homeAway') == 'away'), None)

        if not home_competitor_data or not away_competitor_data:
            print(f"Error: Home or away competitor not found for game {header.get('id')}.")
            return

        home_abv = home_competitor_data['team']['abbreviation']
        away_abv = away_competitor_data['team']['abbreviation']

        # Find the correct team data within the list of teams in the boxscore
        home_team_stats = {s['name']: s.get('displayValue', '0') for s in next((t['statistics'] for t in teams_data if t['team']['abbreviation'] == home_abv), [])}
        away_team_stats = {s['name']: s.get('displayValue', '0') for s in next((t['statistics'] for t in teams_data if t['team']['abbreviation'] == away_abv), [])}

        if not home_team_stats or not away_team_stats:
            print(f"Error: Team stats not found for {home_abv} or {away_abv}.")
            return

        # Check if team objects exist
        if home_abv not in team_objects or away_abv not in team_objects:
            print(f"Error: Team objects for {home_abv} or {away_abv} not found.")
            return

        # Extract and convert stats for the away team
        away_pyds_for = float(away_team_stats.get('netPassingYards', 0))
        away_ryds_for = float(away_team_stats.get('rushingYards', 0))
        away_points_for = float(away_competitor_data.get('score', 0))
        away_giveaways = float(away_team_stats.get('turnovers', 0))
        
        # Extract and convert stats for the home team
        home_pyds_for = float(home_team_stats.get('netPassingYards', 0))
        home_ryds_for = float(home_team_stats.get('rushingYards', 0))
        home_points_for = float(home_competitor_data.get('score', 0))
        home_giveaways = float(home_team_stats.get('turnovers', 0))

        # Infer takeaways from opponent's giveaways
        away_takeaways = home_giveaways
        home_takeaways = away_giveaways

        # Assign yards and points against based on the opponent's stats
        away_pyds_agst = home_pyds_for
        away_ryds_agst = home_ryds_for
        away_points_agst = home_points_for
        
        home_pyds_agst = away_pyds_for
        home_ryds_agst = away_ryds_for
        home_points_agst = away_points_for

        # Get the Team objects
        away_team_obj = team_objects[away_abv]
        home_team_obj = team_objects[home_abv]

        # Update the team objects
        away_team_obj.update_stats(
            pyds_for=away_pyds_for,
            pyds_agst=away_pyds_agst,
            ryds_for=away_ryds_for,
            ryds_agst=away_ryds_agst,
            takeaways=away_takeaways,
            giveaways=away_giveaways,
            points_for=away_points_for,
            points_agst=away_points_agst
        )

        home_team_obj.update_stats(
            pyds_for=home_pyds_for,
            pyds_agst=home_pyds_agst,
            ryds_for=home_ryds_for,
            ryds_agst=home_ryds_agst,
            takeaways=home_takeaways,
            giveaways=home_giveaways,
            points_for=home_points_for,
            points_agst=home_points_agst
        )

        print(f"Updated stats for {away_abv} and {home_abv} based on game data.")

    except (KeyError, ValueError, IndexError) as e:
        print(f"Error parsing game data for game {game_data.get('header', {}).get('id', 'unknown')}: {e}")