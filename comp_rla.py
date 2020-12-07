"""Ballot comparison RLA model."""
import math


ONE_ERROR = .01
TWO_ERROR = .001

class Election:
    def __init__(self, total_votes):
        self.first_place = 0
        self.second_place = 0
        self.total_votes = total_votes

    def count_votes(self, candidate_votes):
        if candidate_votes > self.first_place:
            self.second_place = self.first_place
            self.first_place = candidate_votes
        elif candidate_votes > self.second_place:
            self.second_place = candidate_votes

    def margin(self):
        if self.second_place == 0:
            return 1
        return (self.first_place - self.second_place) / self.total_votes


def multiplier(risk_limit, inflator, tolerance):
    a = 1 / (2 * inflator)
    return math.log(1/risk_limit) / (a + tolerance * math.log(1-a))


def comp_rla(election, risk_limit=0.5, inflator=1.1, tolerance=0.5):

    # tie
    if election.margin() <= 0:
        return [0, election.total_votes, election.total_votes, election.total_votes]

    mult = multiplier(risk_limit, inflator, tolerance)
    margin = election.margin()
    initial_sample = math.ceil(mult / margin)
    expected = initial_sample

    # uncontested
    if margin >= 1:
        return [margin, election.total_votes, initial_sample, expected]

    def ballot_bound(ballots_drawn):
        o_1 = ballots_drawn * ONE_ERROR
        o_2 = ballots_drawn * TWO_ERROR * 5
        u_1 = ballots_drawn * ONE_ERROR * 0.6
        u_2 = ballots_drawn * TWO_ERROR * 4.4
        return (mult + 1.4 * (o_1 + o_2 - u_1 - u_2)) / margin

    draw_lower = ballot_bound(expected)
    while expected < draw_lower and draw_lower < election.total_votes:
        expected += 1
        draw_lower = ballot_bound(expected)
        if draw_lower - expected >= election.total_votes - expected:
            draw_lower = election.total_votes

    if draw_lower >= election.total_votes:
        expected = election.total_votes

    return [margin, election.total_votes, initial_sample, expected]


def simultaneous_rla(election1, election2, risk_limit=0.5, inflator=1.1, tolerance=0.1):

    mult = multiplier(risk_limit, inflator, tolerance)
    margin = min(election1.margin(), election2.margin())
    initial_sample = math.ceil(mult / margin)
    expected = initial_sample
    total_votes = max(election1.total_votes, election2.total_votes)

    # uncontested
    if margin >= 1:
        return [margin, total_votes, initial_sample, expected]

    # # Kaplan-Markov P-Value
    # def km_pval(ballots_drawn):
    #     n_1 = ballots_drawn * ONE_ERROR
    #     n_2 = ballots_drawn * TWO_ERROR
    #     a = pow(1 - margin / 2 / tolerance, ballots_drawn)
    #     b = pow(1 - 1 / 2 / inflator, n_1)
    #     c = pow(1 - 1 / inflator, n_2)
    #     return 1 if b == 0 or c == 0 else a / b / c

    # # if tolerance * margin < ONE_ERROR + TWO_ERROR:
    # pkm = km_pval(expected)
    # while pkm > risk_limit and expected < total_votes:
    #     expected += 1
    #     pkm = km_pval(expected)
    #     if pkm == 1:
    #         expected = total_votes
    #         break

    def ballot_bound(ballots_drawn):
        o_1 = ballots_drawn * ONE_ERROR
        o_2 = ballots_drawn * TWO_ERROR * 5
        u_1 = ballots_drawn * ONE_ERROR * 0.6
        u_2 = ballots_drawn * TWO_ERROR * 4.4
        return (mult + 1.4 * (o_1 + o_2 - u_1 - u_2)) / margin

    draw_lower = ballot_bound(expected)
    while expected < draw_lower and draw_lower < total_votes:
        expected += 1
        draw_lower = ballot_bound(expected)
        if draw_lower - expected >= total_votes - expected:
            draw_lower = total_votes

    if draw_lower >= total_votes:
        expected = total_votes

    return [margin, total_votes, initial_sample, expected]
