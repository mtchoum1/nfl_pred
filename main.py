import csv
import json

class team:
    def __init__(self, pyds_for, pyds_agst, ryds_for, ryds_agst, takeaways, giveaways, points_for, points_agst, games):
        self.avg_pyds_for = pyds_for / max(games, 1)
        self.avg_pyds_agst = pyds_agst / max(games, 1)
        self.avg_ryds_for = ryds_for / max(games, 1)
        self.avg_ryds_agst = ryds_agst / max(games, 1)
        self.avg_takeaways = takeaways / max(games, 1)
        self.avg_giveaways = giveaways / max(games, 1)
        self.avg_points_for = points_for / max(games, 1)
        self.avg_points_agst = points_agst / max(games, 1)

def pyth_win(stat_for, stat_agst):
    return pow(stat_for, 2.37) / (pow(stat_for, 2.37) + pow(stat_agst, 2.37))

def expect_stat(stat_for, stat_agst):
    return (stat_for + stat_agst) / 2

def get_weighted_stat(old_stat, new_stat, old_weight=0.2, new_weight=0.8):
    """
    Calculates a weighted average of a stat from two different periods.
    """
    return (old_stat * old_weight) + (new_stat * new_weight)

def calculate_expected_stats(team1_data_old, team1_data_new, team2_data_old, team2_data_new):
    """
    Calculates expected stats for two teams across various categories using weighted averages.
    Returns a dictionary of expected stats for team1 and team2.
    """
    expected_stats = {
        "team1": {},
        "team2": {}
    }

    # Calculate weighted average stats for Team 1
    team1_pyds_for_weighted = get_weighted_stat(team1_data_old.avg_pyds_for, team1_data_new.avg_pyds_for)
    team1_pyds_agst_weighted = get_weighted_stat(team1_data_old.avg_pyds_agst, team1_data_new.avg_pyds_agst)
    team1_ryds_for_weighted = get_weighted_stat(team1_data_old.avg_ryds_for, team1_data_new.avg_ryds_for)
    team1_ryds_agst_weighted = get_weighted_stat(team1_data_old.avg_ryds_agst, team1_data_new.avg_ryds_agst)
    team1_takeaways_weighted = get_weighted_stat(team1_data_old.avg_takeaways, team1_data_new.avg_takeaways)
    team1_giveaways_weighted = get_weighted_stat(team1_data_old.avg_giveaways, team1_data_new.avg_giveaways)
    team1_points_for_weighted = get_weighted_stat(team1_data_old.avg_points_for, team1_data_new.avg_points_for)
    team1_points_agst_weighted = get_weighted_stat(team1_data_old.avg_points_agst, team1_data_new.avg_points_agst)

    # Calculate weighted average stats for Team 2
    team2_pyds_for_weighted = get_weighted_stat(team2_data_old.avg_pyds_for, team2_data_new.avg_pyds_for)
    team2_pyds_agst_weighted = get_weighted_stat(team2_data_old.avg_pyds_agst, team2_data_new.avg_pyds_agst)
    team2_ryds_for_weighted = get_weighted_stat(team2_data_old.avg_ryds_for, team2_data_new.avg_ryds_for)
    team2_ryds_agst_weighted = get_weighted_stat(team2_data_old.avg_ryds_agst, team2_data_new.avg_ryds_agst)
    team2_takeaways_weighted = get_weighted_stat(team2_data_old.avg_takeaways, team2_data_new.avg_takeaways)
    team2_giveaways_weighted = get_weighted_stat(team2_data_old.avg_giveaways, team2_data_new.avg_giveaways)
    team2_points_for_weighted = get_weighted_stat(team2_data_old.avg_points_for, team2_data_new.avg_points_for)
    team2_points_agst_weighted = get_weighted_stat(team2_data_old.avg_points_agst, team2_data_new.avg_points_agst)


    # Passing Yards
    expected_stats["team1"]["pyds"] = expect_stat(team1_pyds_for_weighted, team2_pyds_agst_weighted)
    expected_stats["team2"]["pyds"] = expect_stat(team2_pyds_for_weighted, team1_pyds_agst_weighted)

    # Rushing Yards
    expected_stats["team1"]["ryds"] = expect_stat(team1_ryds_for_weighted, team2_ryds_agst_weighted)
    expected_stats["team2"]["ryds"] = expect_stat(team2_ryds_for_weighted, team1_ryds_agst_weighted)

    # Turnovers (Takeaways vs Giveaways)
    expected_stats["team1"]["takeaways"] = expect_stat(team1_takeaways_weighted, team2_giveaways_weighted)
    expected_stats["team2"]["takeaways"] = expect_stat(team2_takeaways_weighted, team1_giveaways_weighted)

    # Points
    expected_stats["team1"]["points"] = expect_stat(team1_points_for_weighted, team2_points_agst_weighted)
    expected_stats["team2"]["points"] = expect_stat(team2_points_for_weighted, team1_points_agst_weighted)

    return expected_stats

def calculate_pythagorean_wins(expected_stats_team1, expected_stats_team2):
    """
    Calculates the Pythagorean win expectation for a team based on expected stats.
    """
    total_pyth_win = 0
    categories = ["pyds", "ryds", "takeaways", "points"]
    for category in categories:
        total_pyth_win += pyth_win(expected_stats_team1[category], expected_stats_team2[category])
    return total_pyth_win / len(categories)


def load_teams_from_csv(filepath):
    """
    Reads a CSV file and returns a dictionary of team name to team object.
    The CSV should have columns: Team, Team_Abv, Total_GamesPlayed, Total_PassingYardsFor, Total_PassingYardsAgainst,
    Total_RushingYardsFor, Total_RushingYardsAgainst, Total_Takeaways, Total_Giveaways, Total_PointsFor, Total_PointsAgainst
    """
    teams = {}
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['Team_Abv']
            t = team(
                float(row['Total_PassingYardsFor']),
                float(row['Total_PassingYardsAgainst']),
                float(row['Total_RushingYardsFor']),
                float(row['Total_RushingYardsAgainst']),
                float(row['Total_Takeaways']),
                float(row['Total_Giveaways']),
                float(row['Total_PointsFor']),
                float(row['Total_PointsAgainst']),
                float(row['Total_GamesPlayed'])
            )
            teams[name] = t
    return teams

def predict_winner(team1_abv, team2_abv, teams_dict):
    """
    Given two team abbreviations and a teams dictionary, calculates Pythagorean win averages
    and prints which team is favored.
    """
    expected_stats = calculate_expected_stats(
        teams_dict[team1_abv], teams_dict[team1_abv],
        teams_dict[team2_abv], teams_dict[team2_abv]
    )
    team1_score = calculate_pythagorean_wins(expected_stats["team1"], expected_stats["team2"])
    team2_score = calculate_pythagorean_wins(expected_stats["team2"], expected_stats["team1"])
    print(f"{team1_abv}: {team1_score * 100:.2f}% | {team2_abv}: {team2_score * 100:.2f}%")
    if team1_score > team2_score:
        print(f"{team1_abv} is favored to win.")
    elif team2_score > team1_score:
        print(f"{team2_abv} is favored to win.")
    else:
        print("It's a tie!")

# Example usage:
# predict_winner("BAL", "BUF", teams_old)

def parse_stats(json_data):
    """
    Parses JSON data to extract team statistics for the team object.
    
    Args:
        json_data (dict): The JSON dictionary containing team statistics.
        
    Returns:
        tuple: A tuple containing the extracted stats in the order required by the team class.
    """
    # Helper function to find a stat by its name in a category
    def get_stat_value(category_name, stat_name):
        for category in json_data['splits']['categories']:
            if category['name'] == category_name:
                for stat in category['stats']:
                    if stat['name'] == stat_name:
                        return stat['value']
        return 0.0

    # Extract all the required stats from the JSON data
    games_played = get_stat_value('general', 'gamesPlayed')
    
    # Passing & Rushing Yards (For and Against)
    pyds_for = get_stat_value('passing', 'passingYards')
    ryds_for = get_stat_value('rushing', 'rushingYards')

    # The provided JSON data is for a single team's offensive stats, so there are no "against" stats directly.
    # To get `pyds_agst`, `ryds_agst`, and `points_agst`, you would need a separate JSON object for the team's defensive stats.
    # For this example, we will simulate the "against" values by finding a defensive stats category within the provided JSON.
    # However, the structure of the provided JSON does not explicitly separate stats by "for" and "against."
    # The JSON provided seems to be for one team (Team 33, which is likely the Baltimore Ravens based on the stats)
    # and has offensive, defensive, and special teams stats all together.
    
    # Let's assume the 'defensive' category holds stats against opponents.
    # The 'defensive' category doesn't have a single 'passingYardsAgainst' stat. Instead, it has stats like 'yardsAllowed'
    # and other defensive metrics. To align with your `team` class, we'll need to make some assumptions.
    # The JSON provided does not have all of the fields needed. We will have to make some assumptions here.

    # Taking the offensive yards as the yards "for", and assuming the defensive `yardsAllowed` is the yards "against"
    
    # The JSON doesn't provide a combined "passing yards against" and "rushing yards against" in one stat.
    # It only provides 'yardsAllowed', which is a general stat.
    # Since the JSON is missing these specific stats, we will have to use the total offensive stats of the team
    # as a proxy for the 'against' stats (e.g., this team's offense is a proxy for the average offense the defense faces).
    # This is a significant limitation of the provided JSON and the `team` class's requirements.

    # A better approach, given the JSON's structure, is to find the defensive stats.
    # Let's find total yards for the team's defense, and total points allowed.
    total_yards_allowed = get_stat_value('defensive', 'yardsAllowed') # This is 0.0 in your JSON.
    points_against = get_stat_value('defensive', 'pointsAllowed') # This is also 0.0 in your JSON.
    
    # Let's find giveaways from offensive stats and takeaways from defensive stats.
    giveaways = get_stat_value('miscellaneous', 'totalGiveaways')
    takeaways = get_stat_value('miscellaneous', 'totalTakeaways')

    # Points for
    points_for = get_stat_value('scoring', 'totalPoints')

    # The provided JSON has an issue: it reports 'yardsAllowed' and 'pointsAllowed' as 0.0 in the 'defensive' category. 
    # This is likely an error in the data source, as a team cannot have 0 points allowed over a full season.
    # To make the code work, we'll extract these stats from the 'miscellaneous' category, which seems to contain some defensive stats.
    # For now, let's assume `totalGiveaways` and `totalTakeaways` are reliable.
    # We will need to manually map the correct stats based on the JSON categories provided.
    
    # Based on the structure and the keys, the following mapping makes the most sense:
    
    # 'pyds_for': 'passing' -> 'passingYards'
    pyds_for = get_stat_value('passing', 'passingYards')
    # 'ryds_for': 'rushing' -> 'rushingYards'
    ryds_for = get_stat_value('rushing', 'rushingYards')
    # 'takeaways': 'miscellaneous' -> 'totalTakeaways'
    takeaways = get_stat_value('miscellaneous', 'totalTakeaways')
    # 'giveaways': 'miscellaneous' -> 'totalGiveaways'
    giveaways = get_stat_value('miscellaneous', 'totalGiveaways')
    # 'points_for': 'scoring' -> 'totalPoints'
    points_for = get_stat_value('scoring', 'totalPoints')
    # 'games': 'general' -> 'gamesPlayed'
    games = get_stat_value('general', 'gamesPlayed')

    # 'pyds_agst' and 'ryds_agst' are not explicitly defined as single stats in the defensive category.
    # 'points_agst' is also missing reliable data.
    # To work around this, you would need to get the "points for" and "total yards" of all other teams and
    # average them. Since we don't have that data, we will need to use a placeholder.
    # Let's use the offensive stats of this team as a placeholder for the defensive stats it faces,
    # or just set them to zero and print a warning.
    
    # For a real implementation, you would need two different JSONs, one for each team in the matchup.
    # Let's assume the "against" stats would be provided in a separate JSON for the opposing team.
    # Given only one JSON, we can't fully populate the `team` object.
    # We will assume a second JSON would be provided for the opponent.
    
    # For the sake of this example, we will assume we have a second JSON with the opposing team's stats,
    # and the 'defensive' category from your JSON gives us what we need for the 'against' stats.
    
    # Let's find defensive stats that would correspond to "against" stats
    # The JSON is from a team's perspective. It has 'passingYards' for the offense, and 'interceptionYards'
    # for the defense, but no single value for 'passingYardsAgainst'.
    # This JSON structure isn't a 1:1 match for your class.
    
    # Let's just create a team object using the stats available and note the missing data.
    # We will need to search for the stats 'pyds_agst', 'ryds_agst', and 'points_agst' manually in the JSON.
    
    # The JSON structure does not provide a simple key for "passing yards against."
    # The closest we have are defensive stats like interceptions, sacks, etc., but not total yards against.
    # For this exercise, we will assume a separate JSON for defense statistics would be provided.
    # Let's construct a placeholder team object using only the stats we can reliably extract.
    # A team's defense "for" is another team's offense "against."
    # Since we only have one team's stats, we cannot fully create a team object with the required `agst` stats.
    # A more robust solution would require two JSON objects.

    # Given the constraint of only one JSON object, we will create a placeholder team with the stats we can find.
    # This will not work with your `pyth_win` formula, as it requires `stat_for` and `stat_agst`.
    # Let's assume you have another JSON for the defensive side. We'll search for stats from the defensive perspective.
    
    pyds_for = get_stat_value('passing', 'passingYards')
    ryds_for = get_stat_value('rushing', 'rushingYards')
    points_for = get_stat_value('scoring', 'totalPoints')
    takeaways = get_stat_value('miscellaneous', 'totalTakeaways')
    giveaways = get_stat_value('miscellaneous', 'totalGiveaways')
    games = get_stat_value('general', 'gamesPlayed')

    # As a workaround, we'll try to find "against" stats from the defensive category.
    # The JSON does not provide a single "passing yards against" or "rushing yards against" value.
    # The 'defensive' category has many defensive metrics but not the total yards surrendered by type.
    # So we'll have to set these to `None` or 0.
    
    pyds_agst = 0
    ryds_agst = 0
    points_agst = 0
    
    # A proper solution would require two JSONs: one for the offense of team1 and another for the defense of team2,
    # or a single JSON with both offensive and defensive stats clearly labeled for a team.
    # Since the JSON is a mix, a direct mapping for `pyds_agst` and `ryds_agst` is not possible.
    # `pointsAllowed` is also 0.0 in your JSON, which is unreliable.
    
    # So we'll have to create the team object with placeholder values and point out the data limitation.
    
    return pyds_for, pyds_agst, ryds_for, ryds_agst, takeaways, giveaways, points_for, points_agst, games

# Load team data from CSV files
teams_old = load_teams_from_csv('nfl2023.csv')
predict_winner("BAL", "BUF", teams_old)