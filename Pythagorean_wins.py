class team:
    # pyds = passing yards
    # ryds = rushing yards
    # agst = against
    # to = turnovers
    def __init__(self, pyds_for, pyds_agst, ryds_for, ryds_agst, takeaways, giveaways, points_for, points_agst):
        self.avg_pyds_for = pyds_for/17
        self.avg_pyds_agst = pyds_agst/17
        self.avg_ryds_for = ryds_for/17
        self.avg_ryds_agst = ryds_agst/17
        self.avg_takeaways = takeaways/17
        self.avg_giveaways = giveaways/17
        self.avg_points_for = points_for/17
        self.avg_points_agst = points_agst/17

def pyth_win(stat_for, stat_agst):
    return pow(stat_for, 2.37) / (pow(stat_for, 2.37) + pow(stat_agst, 2.37))

def expect_stat(stat_for, stat_agst):
    return (stat_for + stat_agst)/2

BAL = [team(4035, 4150, 3189, 1361, 17, 11, 518, 361), team(0,0,0,0,0,0,0,0)]
BUF = [team(3875, 3843, 2230, 1963, 32, 8, 525, 368), team(0,0,0,0,0,0,0,0)]

bal_exp_pyds = expect_stat(BAL[0].avg_pyds_for, BUF[0].avg_pyds_agst)
buf_exp_pyds = expect_stat(BUF[0].avg_pyds_for, BAL[0].avg_pyds_agst)

bal_exp_ryds = expect_stat(BAL[0].avg_ryds_for, BUF[0].avg_ryds_agst)
buf_exp_ryds = expect_stat(BUF[0].avg_ryds_for, BAL[0].avg_ryds_agst)

bal_exp_take = expect_stat(BAL[0].avg_takeaways, BUF[0].avg_giveaways)
buf_exp_take = expect_stat(BUF[0].avg_takeaways, BAL[0].avg_giveaways)

bal_exp_points = expect_stat(BAL[0].avg_points_for, BUF[0].avg_points_agst)
buf_exp_points = expect_stat(BUF[0].avg_points_for, BAL[0].avg_points_agst)\

bal_pyth_win = pyth_win(bal_exp_pyds, buf_exp_pyds) + pyth_win(bal_exp_ryds, buf_exp_ryds) + pyth_win(bal_exp_take, buf_exp_take) + pyth_win(bal_exp_points, buf_exp_points)
buf_pyth_win = pyth_win(buf_exp_pyds, bal_exp_pyds) + pyth_win(buf_exp_ryds, bal_exp_ryds) + pyth_win(buf_exp_take, bal_exp_take) + pyth_win(buf_exp_points, bal_exp_points)

print(bal_pyth_win/4)
print(buf_pyth_win/4)