from typing import Dict
import csv

from arlo.server.audit_math.sampler_contest import Contest


class StateElection:
    def __init__(self, year):
        self.year: int = year
        self.pres: Contest = None
        self.senate: Contest = None
        self.house: Dict[int, Contest] = {}  # maps from district to contest

    def total_votes(self):
        total = 0
        if self.pres is not None:
            total += self.pres.ballots
        if self.senate is not None:
            total += self.senate.ballots
        for contest in self.house.values():
            total += contest.ballots
        return total


elections: Dict[int, Dict[str, StateElection]] = {}  # map from year -> map from states -> StateElection

state_pos_dc = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS',
                'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC',
                'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

for year in range(1976, 2020, 2):
    elections[year] = {}
    for state in state_pos_dc:
        elections[year][state] = StateElection(year)

with open('1976-2016-president-headers.csv') as votes_file:
    pres_contest_data: Dict[int, Dict[str, Dict[str, int]]] = {}
    for row in csv.DictReader(votes_file):
        year = int(row['year'])
        if year not in pres_contest_data:
            pres_contest_data[year] = {}
        state = row['state_po']
        if state not in pres_contest_data[year]:
            pres_contest_data[year][state] = {
                'numWinners': 1,
                'votesAllowed': int(row['totalvotes']),
                'ballots': int(row['totalvotes']),
            }
        pres_contest_data[year][state][row['candidate']] = int(row['candidatevotes'])
    for year, state_map in pres_contest_data.items():
        for state, contest_data in state_map.items():
            if year not in elections:
                elections[year] = {}
            if state not in elections[year]:
                elections[year][state] = StateElection(year)
            contest_name = str(year) + '_' + state + '_pres'
            elections[year][state].pres = Contest(contest_name, contest_data)

with open('1976-2018-senate-headers.csv') as votes_file:
    senate_contest_data: Dict[int, Dict[str, Dict[str, int]]] = {}
    for row in csv.DictReader(votes_file):
        # ignore special elections
        if row['special'] != 'FALSE':
            continue
        # ignore non-general elections (only other stage type was "pre", not sure what that means)
        if row['stage'] != 'gen':
            continue
        year = int(row['year'])
        if year not in senate_contest_data:
            senate_contest_data[year] = {}
        state = row['state_po']
        if state not in senate_contest_data[year]:
            senate_contest_data[year][state] = {
                'numWinners': 1,
                'votesAllowed': int(row['totalvotes']),
                'ballots': int(row['totalvotes']),
            }
        senate_contest_data[year][state][row['candidate']] = int(row['candidatevotes'])
    for year, state_map in senate_contest_data.items():
        if year not in elections:
            elections[year] = {}
        for state, contest_data in state_map.items():
            if state not in elections[year]:
                elections[year][state] = StateElection(year)
            if len(contest_data) == 4:  # only 1 candidate
                continue
            contest_name = str(year) + '_' + state + '_senate'
            elections[year][state].senate = Contest(contest_name, contest_data)

with open('1976-2018-house-headers.csv') as votes_file:
    house_contest_data: Dict[int, Dict[str, Dict[int, Dict[str, int]]]] = {}
    for row in csv.DictReader(votes_file):
        # ignore special elections
        if row['special'] != 'FALSE':
            continue
        # ignore non-general elections (only other stage type was "pri", not sure what that means)
        if row['stage'] != 'gen':
            continue
        # ignore runoff elections
        if not (row['runoff'] == 'FALSE' or row['runoff'] == 'NA'):
            continue
        # ignore uncontested elections
        if row['totalvotes'] == '0' or row['totalvotes'] == '1':
            continue
        year = int(row['year'])
        if year not in house_contest_data:
            house_contest_data[year] = {}
        state = row['state_po']
        if state not in house_contest_data[year]:
            house_contest_data[year][state] = {}
        district = int(row['district'])
        if district not in house_contest_data[year][state]:
            house_contest_data[year][state][district] = {
                'numWinners': 1,
                'votesAllowed': int(row['totalvotes']),
                'ballots': int(row['totalvotes']),
            }
        if row['candidate'] not in house_contest_data[year][state][district]:
            house_contest_data[year][state][district][row['candidate']] = 0
        # sum instead of assign to deal with fusion tickets
        house_contest_data[year][state][district][row['candidate']] += int(row['candidatevotes'])
    for year, state_map in house_contest_data.items():
        if year not in elections:
            elections[year] = {}
        for state, district_map in state_map.items():
            if state not in elections[year]:
                elections[year][state] = StateElection(year)
            for district, contest_data in district_map.items():
                contest_name = str(year) + '_' + state + '_house_' + str(district)
                if len(contest_data) == 4:  # only 1 candidate
                    continue
                elections[year][state].house[district] = Contest(contest_name, contest_data)
