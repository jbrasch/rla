import csv
import numpy as np
import matplotlib.pyplot as plt
from comp_rla import Election, comp_rla, simultaneous_rla

import time

class StateElection:
    def __init__(self, year, po):
        self.year = year
        self.po = po
        self.senate = None
        self.pres = None
        self.house = {}


def count_votes(pres_file, senate_file, house_file, min_year, max_year):

    # list of dicts, one per election year, maps state name to StateElection instances
    elections = [{} for _ in range((max_year - min_year) // 2)]

    with open(pres_file) as votes_file:
        for row in csv.reader(votes_file):
            year, name, po = int(row[0]), row[1], row[2]
            name = name.lower().title()
            if name in elections[year % 44 // 2]:
                elections[year % 44 // 2][name].pres.count_votes(int(row[10]))
            else:
                election = StateElection(year, po)
                election.pres = Election(int(row[11]))
                election.pres.count_votes(int(row[10]))
                elections[year % 44 // 2][name] = election


    with open(senate_file) as votes_file:
        for row in csv.reader(votes_file):
            # ignore special elections
            if row[6] != 'FALSE':
                continue
            year, name, po = int(row[0]), row[1], row[2]
            name = name.lower().title()
            if name in elections[year % 44 // 2]:
                if not elections[year % 44 // 2][name].senate:
                    elections[year % 44 // 2][name].senate = Election(int(row[12]))
                elections[year % 44 // 2][name].senate.count_votes(int(row[11]))
            else:
                election = StateElection(year, po)
                election.senate = Election(int(row[12]))
                election.senate.count_votes(int(row[11]))
                elections[year % 44 // 2][name] = election

    with open(house_file, encoding='latin1') as votes_file:
        for row in csv.reader(votes_file):
            # ignore primary, runoff, special elections
            if row[8] != 'gen' or row[9] == 'TRUE' or row[10] == 'TRUE':
                continue
            year, name, po, district = int(row[0]), row[1], row[2], int(row[7])
            name = name.lower().title()
            if name in elections[year % 44 // 2]:
                if district not in elections[year % 44 // 2][name].house:
                    elections[year % 44 // 2][name].house[district] = Election(int(row[16]))
                elections[year % 44 // 2][name].house[district].count_votes(int(row[15]))
            else:
                election = StateElection(year, po)
                election.house[district] = Election(int(row[16]))
                election.house[district].count_votes(int(row[15]))
                elections[year % 44 // 2][name] = election

    return elections


def run_model(elections, ext):

    start_t = time.time()
    # president
    with open(f'pres_{ext}', 'w') as rla_file:
        writer = csv.writer(rla_file)
        writer.writerow(['year', 'state', 'postal code', 'margin', 'total votes', 'initial sample', 'expected sample'])
        for election_year in elections:
            for state_name, state_election in election_year.items():
                if state_election.pres:
                    info = [state_election.year, state_name, state_election.po]
                    results = comp_rla(state_election.pres)
                    info.extend(results)
                    writer.writerow(info)

    # senate
    with open(f'senate_{ext}', 'w') as rla_file:
        writer = csv.writer(rla_file)
        writer.writerow(['year', 'state', 'postal code', 'margin', 'total votes', 'initial sample', 'expected sample'])
        for election_year in elections:
            for state_name, state_election in election_year.items():
                if state_election.senate:
                    info = [state_election.year, state_name, state_election.po]
                    results = comp_rla(state_election.senate)
                    info.extend(results)
                    writer.writerow(info)


    # house
    with open(f'house_{ext}', 'w') as rla_file:
        writer = csv.writer(rla_file)
        writer.writerow(['year', 'state', 'postal code', 'district', 'margin', 'total votes', 'initial sample', 'expected sample'])
        for election_year in elections:
            for state_name, district_elections in election_year.items():
                for district, election in district_elections.house.items():
                    info = [district_elections.year, state_name, district_elections.po, district]
                    results = comp_rla(election)
                    info.extend(results)
                    writer.writerow(info)

    # pres & senate
    with open(f'pres-senate_{ext}', 'w') as rla_file:
        writer = csv.writer(rla_file)
        writer.writerow(['year', 'state', 'postal code', 'margin', 'total votes', 'initial sample', 'expected sample'])
        for election_year in elections:
            for state_name, state_election in election_year.items():
                info = [state_election.year, state_name, state_election.po]
                # senate race in state ~ 33/50
                if state_election.senate and state_election.pres:
                    results = simultaneous_rla(state_election.pres, state_election.senate)
                    info.extend(results)
                    writer.writerow(info)
                # only electing president
                elif state_election.pres:
                    results = comp_rla(state_election.pres)
                    info.extend(results)
                    writer.writerow(info)

    print((time.time()-start_t)/60)


ELECTIONS = count_votes('1976-2016-president.csv', '1976-2018-senate.csv', '1976-2018-house3.csv', 1976, 2020)
run_model(ELECTIONS, 'comp_rla.csv')
