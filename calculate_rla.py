import csv
import random
import copy
import itertools

import numpy as np

from arlo.server.audit_math.sampler_contest import Contest
import arlo.server.audit_math.bravo as bravo

from construct_contests import elections, StateElection

states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
          'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
          'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
          'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
          'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
          'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
          'West Virginia', 'Wisconsin', 'Wyoming']
state_pos = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY',
             'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH',
             'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

iterations = 2
risk_limit = 10


# {'asn': {'type': 'ASN', 'size': 36, 'prob': 0.53}, '0.7': {'type': None, 'size': 58, 'prob': 0.7}, '0.8': {'type': None, 'size': 79, 'prob': 0.8}, '0.9': {'type': None, 'size': 120, 'prob': 0.9}}


# random selects a candidate from the contest, weighted by unpulled ballots
def select_candidate(contest: Contest, sample_results):
    candidates = list(contest.candidates.keys())
    weights = [contest.candidates[x] - sample_results[x] for x in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def simulate_individual_rla(contest: Contest):
    counts = []
    if 'all-ballots' in bravo.get_sample_size(risk_limit, contest, None):
        for i in range(0, iterations):
            counts.append(contest.ballots)
        return np.array(counts)

    sample_results = copy.deepcopy(contest.candidates)
    arlo_sample_results = {'1': sample_results}
    for i in range(0, iterations):
        for k in sample_results.keys():
            sample_results[k] = 0
        risk, audit_finished = bravo.compute_risk(risk_limit, contest, arlo_sample_results)
        ballots_pulled = 0
        while not audit_finished:
            candidate = select_candidate(contest, sample_results)
            sample_results[candidate] += 1
            ballots_pulled += 1
            risk, audit_finished = bravo.compute_risk(risk_limit, contest, arlo_sample_results)
        counts.append(ballots_pulled)
    return np.array(counts)


def run_rla_simulation():
    with open('arlo_results/arlo-ballot-poll-total_' + str(risk_limit) + '_avg.csv', 'w') as arlo_total_avg, \
            open('arlo_results/arlo-ballot-poll-total_' + str(risk_limit) + '_std.csv', 'w') as arlo_total_std, \
            open('arlo_results/arlo-ballot-poll-pres_' + str(risk_limit) + '_avg.csv', 'w') as arlo_pres_avg, \
            open('arlo_results/arlo-ballot-poll-pres_' + str(risk_limit) + '_std.csv', 'w') as arlo_pres_std, \
            open('arlo_results/arlo-ballot-poll-senate_' + str(risk_limit) + '_avg.csv', 'w') as arlo_senate_avg, \
            open('arlo_results/arlo-ballot-poll-senate_' + str(risk_limit) + '_std.csv', 'w') as arlo_senate_std, \
            open('arlo_results/arlo-ballot-poll-house_' + str(risk_limit) + '_avg.csv', 'w') as arlo_house_avg, \
            open('arlo_results/arlo-ballot-poll-house_' + str(risk_limit) + '_std.csv', 'w') as arlo_house_std:
        total_indv_fieldnames = ['year'] + state_pos
        arlo_total_avg_csv = csv.DictWriter(arlo_total_avg, fieldnames=total_indv_fieldnames)
        arlo_total_avg_csv.writeheader()
        arlo_total_std_csv = csv.DictWriter(arlo_total_std, fieldnames=total_indv_fieldnames)
        arlo_total_std_csv.writeheader()

        arlo_pres_avg_csv = csv.DictWriter(arlo_pres_avg, fieldnames=total_indv_fieldnames)
        arlo_pres_avg_csv.writeheader()
        arlo_pres_std_csv = csv.DictWriter(arlo_pres_std, fieldnames=total_indv_fieldnames)
        arlo_pres_std_csv.writeheader()

        arlo_senate_avg_csv = csv.DictWriter(arlo_senate_avg, fieldnames=total_indv_fieldnames)
        arlo_senate_avg_csv.writeheader()
        arlo_senate_std_csv = csv.DictWriter(arlo_senate_std, fieldnames=total_indv_fieldnames)
        arlo_senate_std_csv.writeheader()

        arlo_house_avg_csv = csv.DictWriter(arlo_house_avg, fieldnames=total_indv_fieldnames)
        arlo_house_avg_csv.writeheader()
        arlo_house_std_csv = csv.DictWriter(arlo_house_std, fieldnames=total_indv_fieldnames)
        arlo_house_std_csv.writeheader()

        for year in range(2016, 2020, 2):
            row_total_avg, row_total_std = [year], [year]
            row_pres_avg, row_pres_std = [year], [year]
            row_senate_avg, row_senate_std = [year], [year]
            row_house_avg, row_house_std = [year], [year]
            pres_year = False
            for state_po in state_pos:
                print(year, state_po)
                election = elections[year][state_po]
                pres = None if election.pres is None else simulate_individual_rla(election.pres)
                senate = None if election.senate is None else simulate_individual_rla(election.senate)
                house = []
                for contest in election.house.values():
                    house.append(simulate_individual_rla(contest))
                if len(house) == 0:
                    house = None
                else:
                    house = np.sum(house, axis=0)

                total = []
                if pres is not None:
                    pres_year = True
                    total.append(pres)
                    row_pres_avg.append(np.average(pres))
                    row_pres_std.append(np.std(pres))
                else:
                    row_pres_avg.append("")
                    row_pres_std.append("")

                if senate is not None:
                    total.append(senate)
                    row_senate_avg.append(np.average(senate))
                    row_senate_std.append(np.std(senate))
                else:
                    row_pres_avg.append("")
                    row_pres_std.append("")

                if house is not None:
                    total.append(house)
                    row_house_avg.append(np.average(house))
                    row_house_std.append(np.std(house))
                else:
                    row_house_avg.append("")
                    row_house_std.append("")

                if len(total) == 0:
                    row_total_avg.append("")
                    row_total_std.append("")
                else:
                    total = np.sum(total, axis=0)
                    row_total_avg.append(np.average(total))
                    row_total_std.append(np.std(total))
            arlo_total_avg_csv.writerow(row_total_avg)
            arlo_total_std_csv.writerow(row_total_std)
            arlo_pres_avg_csv.writerow(row_pres_avg)
            arlo_pres_std_csv.writerow(row_pres_std)
            arlo_senate_avg_csv.writerow(row_senate_avg)
            arlo_senate_std_csv.writerow(row_senate_std)
            arlo_house_avg_csv.writerow(row_house_avg)
            arlo_house_std_csv.writerow(row_house_std)


run_rla_simulation()
