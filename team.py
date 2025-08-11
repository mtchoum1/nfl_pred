from math import pow

class Team:
    """
    Represents an NFL team's average statistics for various categories.
    """
    def __init__(self, pyds_for, pyds_agst, ryds_for, ryds_agst, takeaways, giveaways, points_for, points_agst, games):
        valid_games = max(games, 1)
        self.avg_pyds_for = pyds_for / valid_games
        self.avg_pyds_agst = pyds_agst / valid_games
        self.avg_ryds_for = ryds_for / valid_games
        self.avg_ryds_agst = ryds_agst / valid_games
        self.avg_takeaways = takeaways / valid_games
        self.avg_giveaways = giveaways / valid_games
        self.avg_points_for = points_for / valid_games
        self.avg_points_agst = points_agst / valid_games

def pyth_win(stat_for, stat_agst):
    denominator = pow(stat_for, 2.37) + pow(stat_agst, 2.37)
    if denominator == 0:
        return 0.5
    return pow(stat_for, 2.37) / denominator

def expect_stat(stat_for, stat_agst):
    return (stat_for + stat_agst) / 2

def get_weighted_stat(old_stat, new_stat, old_weight=0.2, new_weight=0.8):
    return (old_stat * old_weight) + (new_stat * new_weight)