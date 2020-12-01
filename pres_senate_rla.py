import csv
import math


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
            return math.inf
        return self.first_place - self.second_place

    def proportional_margin(self):
        return math.inf if self.total_votes == 0 else self.margin() / self.total_votes


class StateElection:
    def __init__(self, year):
        self.year = year
        self.senate = None
        self.pres = None

    def total_votes(self):
        if not self.simultaneous():
            return self.pres.total_votes if self.pres else self.senate.total_votes
        return max(self.senate.total_votes, self.pres.total_votes)

    # mu
    def diluted_margin(self):
        if self.simultaneous():
            if self.total_votes() == 0:
                return math.inf
            return min(self.senate.margin(),self.pres.margin()) / self.total_votes()
        return self.pres.proportional_margin() if self.pres else self.senate.proportional_margin()

    def simultaneous(self):
        return bool(self.senate and self.pres)


# list of dicts, one per election year, maps state name to StateElection instances 
CombinedElections = [{} for _ in range((2020 - 1976) // 2)]

with open('1976-2016-president.csv') as votes_file:
    for row in csv.reader(votes_file):
        year, name = int(row[0]), row[1]
        if name in CombinedElections[year % 44 // 2]:
            CombinedElections[year % 44 // 2][name].pres.count_votes(int(row[10]))
        else:
            election = StateElection(year)
            election.pres = Election(int(row[11]))
            election.pres.count_votes(int(row[10]))
            CombinedElections[year % 44 // 2][name] = election


with open('1976-2018-senate.csv') as votes_file:
    for row in csv.reader(votes_file):
        # ignore special elections
        if row[6] != 'FALSE':
            continue
        year, name = int(row[0]), row[1]
        if name in CombinedElections[year % 44 // 2]:
            if not CombinedElections[year % 44 // 2][name].senate:
                CombinedElections[year % 44 // 2][name].senate = Election(int(row[12]))
            CombinedElections[year % 44 // 2][name].senate.count_votes(int(row[11]))
        else:
            election = StateElection(year)
            election.senate = Election(int(row[12]))
            election.senate.count_votes(int(row[11]))
            CombinedElections[year % 44 // 2][name] = election


with open('1976-2018-pres-senate-rla.csv', 'w') as rla_file:
    writer = csv.writer(rla_file)
    writer.writerow(['year', 'state', 'simultaneous', 'margin', 'initial sample', 'total votes', 'overstatement tolerable', 'expected sample'])
    # from Start 2010b
    multiplier = 5.85
    for election_year in CombinedElections:
        expected_ballots = 0
        total_ballots = 0
        year = 0
        for state, election in election_year.items():
            # initial sample size
            # how many errors can we tolerate? with constnats from Start 2010b
            if election.diluted_margin() == 0:
                initial_sample = election.total_votes()
                overstatement = 0
            elif election.diluted_margin() >= 1:
                initial_sample = 0
                overstatement = election.total_votes()
            else:
                initial_sample = multiplier / election.diluted_margin() if election.simultaneous() else math.ceil(6.2/election.diluted_margin())
                overstatement = math.ceil(.1 * election.diluted_margin() * election.total_votes())

            initial_sample = math.ceil(initial_sample)
            overstatement = math.ceil(overstatement)

            # upper bound -> assume full recount if initial sample if insufficient
            expected = initial_sample if overstatement >= initial_sample else election.total_votes()
    
            writer.writerow([election.year, state, election.simultaneous(), election.diluted_margin(), initial_sample, election.total_votes(), overstatement, expected])
            
            expected_ballots += expected
            total_ballots += election.total_votes()
            year = election.year

        writer.writerow([year, 'USA Total', '', '', '', total_ballots, '', expected_ballots])
