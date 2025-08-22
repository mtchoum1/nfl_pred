import math

# --- Team Statistics Class ---
class Team:
    """
    Represents a team and holds its cumulative statistics for a season.
    """
    def __init__(self, pyds_for=0, pyds_agst=0, ryds_for=0, ryds_agst=0, 
                 takeaways=0, giveaways=0, points_for=0, points_agst=0, 
                 pass_attempts=0, rush_attempts=0, games=0):
        self.pyds_for = float(pyds_for)
        self.pyds_agst = float(pyds_agst)
        self.ryds_for = float(ryds_for)
        self.ryds_agst = float(ryds_agst)
        self.takeaways = float(takeaways)
        self.giveaways = float(giveaways)
        self.points_for = float(points_for)
        self.points_agst = float(points_agst)
        self.pass_attempts = float(pass_attempts)
        self.rush_attempts = float(rush_attempts)
        self.games = float(games) if games > 0 else 0

    def add_game(self, pyds_for, pyds_agst, ryds_for, ryds_agst, 
                 takeaways, giveaways, points_for, points_agst,
                 pass_attempts, rush_attempts):
        """
        Adds the stats from a single game to the team's cumulative totals.
        """
        self.pyds_for += pyds_for
        self.pyds_agst += pyds_agst
        self.ryds_for += ryds_for
        self.ryds_agst += ryds_agst
        self.takeaways += takeaways
        self.giveaways += giveaways
        self.points_for += points_for
        self.points_agst += points_agst
        self.pass_attempts += pass_attempts
        self.rush_attempts += rush_attempts
        self.games += 1

    # Properties to calculate averages, avoiding division by zero
    @property
    def avg_pyds_for(self):
        return self.pyds_for / self.games if self.games > 0 else 0
    @property
    def avg_pyds_agst(self):
        return self.pyds_agst / self.games if self.games > 0 else 0
    @property
    def avg_ryds_for(self):
        return self.ryds_for / self.games if self.games > 0 else 0
    @property
    def avg_ryds_agst(self):
        return self.ryds_agst / self.games if self.games > 0 else 0
    @property
    def avg_takeaways(self):
        return self.takeaways / self.games if self.games > 0 else 0
    @property
    def avg_giveaways(self):
        return self.giveaways / self.games if self.games > 0 else 0
    @property
    def avg_points_for(self):
        return self.points_for / self.games if self.games > 0 else 0
    @property
    def avg_points_agst(self):
        return self.points_agst / self.games if self.games > 0 else 0
    @property
    def avg_pass_attempts(self):
        return self.pass_attempts / self.games if self.games > 0 else 0
    @property
    def avg_rush_attempts(self):
        return self.rush_attempts / self.games if self.games > 0 else 0

# --- Prediction Algorithm Helper Functions ---

def pyth_win(val_for, val_agst):
    """
    Calculates the Pythagorean win expectation for a given statistic.
    """
    if val_for + val_agst == 0:
        return 0.5
    return val_for**2 / (val_for**2 + val_agst**2)

def expect_stat(off_stat, def_stat):
    """
    Calculates the expected outcome of a stat when an offense meets a defense.
    """
    return (off_stat + def_stat) / 2

def get_weighted_stat(old_stat, new_stat, week):
    """
    Calculates a dynamic weighted average of a statistic from the previous season ('old')
    and the current season ('new'). The weight of the new season's stats increases as the
    season progresses.
    """
    if new_stat == 0 or week == 1:
        return old_stat
        
    # As the week number increases, the weight of the new season's stats grows.
    # We cap the new season's weight at 85% to ensure historical data always has some influence.
    new_season_weight = min(((week - 1) / 17.0), 0.85)
    old_season_weight = 1 - new_season_weight
    
    return (old_stat * old_season_weight) + (new_stat * new_season_weight)

# --- JSON Parsing Function ---

def parse_game_json(data, teams_dict):
    """
    Parses the boxscore JSON from the ESPN API to extract game stats and
    updates the provided dictionary of Team objects.
    """
    try:
        boxscore = data.get('boxscore', {})
        team_stats = boxscore.get('teams', [])
        
        if len(team_stats) != 2:
            print("Error: Boxscore doesn't contain two teams.")
            return

        def get_stat_value(stats_list, name):
            stat_item = next((s for s in stats_list if s.get('name') == name), None)
            if not stat_item: return 0.0
            try:
                return float(stat_item.get('value'))
            except (ValueError, TypeError):
                display_value = stat_item.get('displayValue', '0')
                try:
                    return float(display_value.split('-')[0].split('/')[0])
                except (ValueError, TypeError):
                    return 0.0

        def get_stat_display_value(stats_list, name):
            stat_item = next((s for s in stats_list if s.get('name') == name), None)
            return stat_item.get('displayValue') if stat_item else "0/0"

        team1_data, team2_data = team_stats[0], team_stats[1]
        team1_stats, team2_stats = team1_data.get('statistics', []), team2_data.get('statistics', [])
        team1_abv = team1_data.get('team', {}).get('abbreviation')
        team2_abv = team2_data.get('team', {}).get('abbreviation')

        if not all([team1_abv, team2_abv, team1_abv in teams_dict, team2_abv in teams_dict]):
            print(f"Error: Team abbreviation not found. Found: {team1_abv}, {team2_abv}")
            return
            
        header_competitors = data.get('header', {}).get('competitions', [{}])[0].get('competitors', [])
        team1_score = float(next((c.get('score', 0) for c in header_competitors if c.get('team', {}).get('id') == team1_data['team']['id']), 0))
        team2_score = float(next((c.get('score', 0) for c in header_competitors if c.get('team', {}).get('id') == team2_data['team']['id']), 0))

        t1_pyds = get_stat_value(team1_stats, 'netPassingYards')
        t1_ryds = get_stat_value(team1_stats, 'rushingYards')
        t1_giveaways = get_stat_value(team1_stats, 'turnovers')
        t1_rush_attempts = get_stat_value(team1_stats, 'rushingAttempts')
        t1_pass_attempts_str = get_stat_display_value(team1_stats, 'completionAttempts')
        t1_pass_attempts = float(t1_pass_attempts_str.split('/')[1]) if '/' in t1_pass_attempts_str else 0

        t2_pyds = get_stat_value(team2_stats, 'netPassingYards')
        t2_ryds = get_stat_value(team2_stats, 'rushingYards')
        t2_giveaways = get_stat_value(team2_stats, 'turnovers')
        t2_rush_attempts = get_stat_value(team2_stats, 'rushingAttempts')
        t2_pass_attempts_str = get_stat_display_value(team2_stats, 'completionAttempts')
        t2_pass_attempts = float(t2_pass_attempts_str.split('/')[1]) if '/' in t2_pass_attempts_str else 0

        teams_dict[team1_abv].add_game(
            pyds_for=t1_pyds, pyds_agst=t2_pyds, ryds_for=t1_ryds, ryds_agst=t2_ryds,
            takeaways=t2_giveaways, giveaways=t1_giveaways, points_for=team1_score, 
            points_agst=team2_score, pass_attempts=t1_pass_attempts, rush_attempts=t1_rush_attempts
        )
        teams_dict[team2_abv].add_game(
            pyds_for=t2_pyds, pyds_agst=t1_pyds, ryds_for=t2_ryds, ryds_agst=t1_ryds,
            takeaways=t1_giveaways, giveaways=t2_giveaways, points_for=team2_score, 
            points_agst=team1_score, pass_attempts=t2_pass_attempts, rush_attempts=t2_rush_attempts
        )
        
        print(f"Successfully updated stats for {team1_abv} vs {team2_abv}")

    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"Error parsing game JSON: {e}")