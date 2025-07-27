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

# Team Data - Now with two team objects for each team to represent old and new stats
BAL = [team(4035, 4150, 3189, 1361, 17, 11, 518, 361, 17), team(0,0,0,0,0,0,0,0,0)] # Example new stats for BAL
BUF = [team(3875, 3843, 2230, 1963, 32, 8, 525, 368, 17), team(0,0,0,0,0,0,0,0,0)] # Example new stats for BUF

# Calculate expected stats for BAL vs BUF using both old and new data
expected_game_stats = calculate_expected_stats(BAL[0], BAL[1], BUF[0], BUF[1])

# Calculate Pythagorean wins for each team
team1_pyth_win_avg = calculate_pythagorean_wins(expected_game_stats["team1"], expected_game_stats["team2"])
team2_pyth_win_avg = calculate_pythagorean_wins(expected_game_stats["team2"], expected_game_stats["team1"])

print(f"Team 1 wins with {team1_pyth_win_avg}% and Team 2 wins with {team2_pyth_win_avg}%")