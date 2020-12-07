import csv
import random
import copy
import math
from decimal import Decimal

import numpy as np

from arlo.server.audit_math.sampler_contest import Contest
import arlo.server.audit_math.bravo as bravo

from construct_contests import elections

states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
          'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
          'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
          'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
          'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
          'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
          'West Virginia', 'Wisconsin', 'Wyoming']
states_dc = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
             'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas',
             'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
             'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
             'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
             'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
             'West Virginia', 'Wisconsin', 'Wyoming']

state_pos = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY',
             'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH',
             'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
state_pos_dc = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS',
                'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC',
                'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
iterations = 50
risk_limit = 5


# bravo code does a full recount under two conditions:
# (1) if a sample size achieving a 90% chance of completing the RLA would take more than 25% of the total ballots
# and (2) The total ballots is more than 100,000
# We could adjust these parameters if needed.

# {'asn': {'type': 'ASN', 'size': 36, 'prob': 0.53}, '0.7': {'type': None, 'size': 58, 'prob': 0.7}, '0.8': {'type':
# None, 'size': 79, 'prob': 0.8}, '0.9': {'type': None, 'size': 120, 'prob': 0.9}}


# random selects a candidate from the contest, weighted by unpulled ballots
def select_candidate(contest: Contest, sample_results):
    candidates = list(contest.candidates.keys())
    weights = [contest.candidates[x] - sample_results[x] for x in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def simulate_rla(contest: Contest):
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
            sample = bravo.get_sample_size(risk_limit, contest, arlo_sample_results)
            # if our last sample got us to the point where doing a full recount is more efficient, do that
            if 'all-ballots' in sample:
                ballots_pulled = contest.ballots
                break
            # otherwise sample 'size' ballots
            size = sample['asn']['size']
            ballots_pulled += size
            for j in range(0, size):
                candidate = select_candidate(contest, sample_results)
                sample_results[candidate] += 1
            risk, audit_finished = bravo.compute_risk(risk_limit, contest, arlo_sample_results)
        counts.append(ballots_pulled)
    return np.array(counts)


def simulate_rla_individual(contest: Contest):
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


def get_sample_count(sample, percent_f):
    if 'all-ballots' in sample:
        return sample['all-ballots']['size']
    else:
        return sample[percent_f]['size']


def run_rla_sim_poll():
    with open('arlo_results/arlo-ballot-poll-all-' + str(risk_limit) + '-avg.csv', 'w') as arlo_all_avg, \
            open('arlo_results/arlo-ballot-poll-all-' + str(risk_limit) + '-std.csv', 'w') as arlo_all_std, \
            open('arlo_results/arlo-ballot-poll-pres-' + str(risk_limit) + '-avg.csv', 'w') as arlo_pres_avg, \
            open('arlo_results/arlo-ballot-poll-pres-' + str(risk_limit) + '-std.csv', 'w') as arlo_pres_std, \
            open('arlo_results/arlo-ballot-poll-senate-' + str(risk_limit) + '-avg.csv', 'w') as arlo_senate_avg, \
            open('arlo_results/arlo-ballot-poll-senate-' + str(risk_limit) + '-std.csv', 'w') as arlo_senate_std, \
            open('arlo_results/arlo-ballot-poll-house-' + str(risk_limit) + '-avg.csv', 'w') as arlo_house_avg, \
            open('arlo_results/arlo-ballot-poll-house-' + str(risk_limit) + '-std.csv', 'w') as arlo_house_std:
        all_indv_fieldnames = ['year', 'total'] + state_pos
        all_indv_fieldnames_dc = ['year', 'total'] + state_pos_dc
        arlo_all_avg_csv = csv.DictWriter(arlo_all_avg, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_all_avg_csv.writeheader()
        arlo_all_std_csv = csv.DictWriter(arlo_all_std, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_all_std_csv.writeheader()

        arlo_pres_avg_csv = csv.DictWriter(arlo_pres_avg, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_pres_avg_csv.writeheader()
        arlo_pres_std_csv = csv.DictWriter(arlo_pres_std, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_pres_std_csv.writeheader()

        arlo_senate_avg_csv = csv.DictWriter(arlo_senate_avg, fieldnames=all_indv_fieldnames, restval=0)
        arlo_senate_avg_csv.writeheader()
        arlo_senate_std_csv = csv.DictWriter(arlo_senate_std, fieldnames=all_indv_fieldnames, restval=0)
        arlo_senate_std_csv.writeheader()

        arlo_house_avg_csv = csv.DictWriter(arlo_house_avg, fieldnames=all_indv_fieldnames, restval=0)
        arlo_house_avg_csv.writeheader()
        arlo_house_std_csv = csv.DictWriter(arlo_house_std, fieldnames=all_indv_fieldnames, restval=0)
        arlo_house_std_csv.writeheader()

        for year in range(1976, 2020, 2):
            row_all_avg, row_all_std = {'year': year}, {'year': year}
            row_pres_avg, row_pres_std = {'year': year}, {'year': year}
            row_senate_avg, row_senate_std = {'year': year}, {'year': year}
            row_house_avg, row_house_std = {'year': year}, {'year': year}
            pres_year = year % 4 == 0
            all_total, pres_total, senate_total, house_total = [], [], [], []
            for state_po in state_pos_dc:
                print(year, state_po)
                if not pres_year and state_po == 'DC':
                    continue
                election = elections[year][state_po]
                assert pres_year == (election.pres is not None)
                try:
                    pres = None if election.pres is None else simulate_rla(election.pres)
                    senate = None if election.senate is None else simulate_rla(election.senate)
                    house = []
                    for contest in election.house.values():
                        house.append(simulate_rla(contest))
                except Exception as e:
                    print(e)
                    print(contest.name)
                    print(contest.candidates)
                    raise e

                if len(house) == 0:
                    house = None
                else:
                    house = np.sum(house, axis=0)

                all_races = []
                if pres_year:
                    all_races.append(pres)
                    pres_total.append(pres)
                    row_pres_avg[state_po] = math.ceil(np.average(pres))
                    row_pres_std[state_po] = math.ceil(np.std(pres))
                if senate is not None:
                    all_races.append(senate)
                    senate_total.append(senate)
                    row_senate_avg[state_po] = math.ceil(np.average(senate))
                    row_senate_std[state_po] = math.ceil(np.std(senate))
                if house is not None:
                    all_races.append(house)
                    house_total.append(house)
                    row_house_avg[state_po] = math.ceil(np.average(house))
                    row_house_std[state_po] = math.ceil(np.std(house))

                all_races = np.sum(all_races, axis=0)
                all_total.append(all_races)
                row_all_avg[state_po] = math.ceil(np.average(all_races))
                row_all_std[state_po] = math.ceil(np.std(all_races))

            all_total, senate_total, house_total = np.sum(all_total, axis=0), \
                                                   np.sum(senate_total, axis=0), \
                                                   np.sum(house_total, axis=0)
            if pres_year:
                pres_total = np.sum(pres_total, axis=0)

            row_all_avg['total'] = math.ceil(np.average(all_total))
            row_all_std['total'] = math.ceil(np.std(all_total))
            if pres_year:
                row_pres_avg['total'] = math.ceil(np.average(pres_total))
                row_pres_std['total'] = math.ceil(np.std(pres_total))
            row_senate_avg['total'] = math.ceil(np.average(senate_total))
            row_senate_std['total'] = math.ceil(np.std(senate_total))
            row_house_avg['total'] = math.ceil(np.average(house_total))
            row_house_std['total'] = math.ceil(np.std(house_total))

            arlo_all_avg_csv.writerow(row_all_avg)
            arlo_all_std_csv.writerow(row_all_std)
            if pres_year:
                arlo_pres_avg_csv.writerow(row_pres_avg)
                arlo_pres_std_csv.writerow(row_pres_std)
            arlo_senate_avg_csv.writerow(row_senate_avg)
            arlo_senate_std_csv.writerow(row_senate_std)
            arlo_house_avg_csv.writerow(row_house_avg)
            arlo_house_std_csv.writerow(row_house_std)

            arlo_all_avg.flush()
            arlo_all_std.flush()
            if pres_year:
                arlo_pres_avg.flush()
                arlo_pres_std.flush()
            arlo_senate_avg.flush()
            arlo_senate_std.flush()
            arlo_house_avg.flush()
            arlo_house_std.flush()


def run_rla_sim_poll_indv():
    with open('arlo_results/arlo-ballot-poll-all-indv-' + str(risk_limit) + '-avg.csv', 'w') as arlo_all_avg, \
            open('arlo_results/arlo-ballot-poll-all-indv-' + str(risk_limit) + '-std.csv', 'w') as arlo_all_std, \
            open('arlo_results/arlo-ballot-poll-pres-indv-' + str(risk_limit) + '-avg.csv', 'w') as arlo_pres_avg, \
            open('arlo_results/arlo-ballot-poll-pres-indv-' + str(risk_limit) + '-std.csv', 'w') as arlo_pres_std, \
            open('arlo_results/arlo-ballot-poll-senate-indv-' + str(risk_limit) + '-avg.csv', 'w') as arlo_senate_avg, \
            open('arlo_results/arlo-ballot-poll-senate-indv-' + str(risk_limit) + '-std.csv', 'w') as arlo_senate_std, \
            open('arlo_results/arlo-ballot-poll-house-indv-' + str(risk_limit) + '-avg.csv', 'w') as arlo_house_avg, \
            open('arlo_results/arlo-ballot-poll-house-indv-' + str(risk_limit) + '-std.csv', 'w') as arlo_house_std:
        all_indv_fieldnames = ['year', 'total'] + state_pos
        all_indv_fieldnames_dc = ['year', 'total'] + state_pos_dc
        arlo_all_avg_csv = csv.DictWriter(arlo_all_avg, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_all_avg_csv.writeheader()
        arlo_all_std_csv = csv.DictWriter(arlo_all_std, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_all_std_csv.writeheader()

        arlo_pres_avg_csv = csv.DictWriter(arlo_pres_avg, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_pres_avg_csv.writeheader()
        arlo_pres_std_csv = csv.DictWriter(arlo_pres_std, fieldnames=all_indv_fieldnames_dc, restval=0)
        arlo_pres_std_csv.writeheader()

        arlo_senate_avg_csv = csv.DictWriter(arlo_senate_avg, fieldnames=all_indv_fieldnames, restval=0)
        arlo_senate_avg_csv.writeheader()
        arlo_senate_std_csv = csv.DictWriter(arlo_senate_std, fieldnames=all_indv_fieldnames, restval=0)
        arlo_senate_std_csv.writeheader()

        arlo_house_avg_csv = csv.DictWriter(arlo_house_avg, fieldnames=all_indv_fieldnames, restval=0)
        arlo_house_avg_csv.writeheader()
        arlo_house_std_csv = csv.DictWriter(arlo_house_std, fieldnames=all_indv_fieldnames, restval=0)
        arlo_house_std_csv.writeheader()

        for year in range(1976, 2020, 2):
            row_all_avg, row_all_std = {'year': year}, {'year': year}
            row_pres_avg, row_pres_std = {'year': year}, {'year': year}
            row_senate_avg, row_senate_std = {'year': year}, {'year': year}
            row_house_avg, row_house_std = {'year': year}, {'year': year}
            pres_year = year % 4 == 0
            all_total, pres_total, senate_total, house_total = [], [], [], []
            for state_po in state_pos_dc:
                print(year, state_po)
                if not pres_year and state_po == 'DC':
                    continue
                election = elections[year][state_po]
                assert pres_year == (election.pres is not None)
                try:
                    pres = None if election.pres is None else simulate_rla(election.pres)
                    senate = None if election.senate is None else simulate_rla(election.senate)
                    house = []
                    for contest in election.house.values():
                        house.append(simulate_rla(contest))
                except Exception as e:
                    print(e)
                    print(contest.name)
                    print(contest.candidates)
                    raise e

                if len(house) == 0:
                    house = None
                else:
                    house = np.sum(house, axis=0)

                all_races = []
                if pres_year:
                    all_races.append(pres)
                    pres_total.append(pres)
                    row_pres_avg[state_po] = math.ceil(np.average(pres))
                    row_pres_std[state_po] = math.ceil(np.std(pres))
                if senate is not None:
                    all_races.append(senate)
                    senate_total.append(senate)
                    row_senate_avg[state_po] = math.ceil(np.average(senate))
                    row_senate_std[state_po] = math.ceil(np.std(senate))
                if house is not None:
                    all_races.append(house)
                    house_total.append(house)
                    row_house_avg[state_po] = math.ceil(np.average(house))
                    row_house_std[state_po] = math.ceil(np.std(house))

                all_races = np.sum(all_races, axis=0)
                all_total.append(all_races)
                row_all_avg[state_po] = math.ceil(np.average(all_races))
                row_all_std[state_po] = math.ceil(np.std(all_races))

            all_total, senate_total, house_total = np.sum(all_total, axis=0), \
                                                   np.sum(senate_total, axis=0), \
                                                   np.sum(house_total, axis=0)
            if pres_year:
                pres_total = np.sum(pres_total, axis=0)

            row_all_avg['total'] = math.ceil(np.average(all_total))
            row_all_std['total'] = math.ceil(np.std(all_total))
            if pres_year:
                row_pres_avg['total'] = math.ceil(np.average(pres_total))
                row_pres_std['total'] = math.ceil(np.std(pres_total))
            row_senate_avg['total'] = math.ceil(np.average(senate_total))
            row_senate_std['total'] = math.ceil(np.std(senate_total))
            row_house_avg['total'] = math.ceil(np.average(house_total))
            row_house_std['total'] = math.ceil(np.std(house_total))

            arlo_all_avg_csv.writerow(row_all_avg)
            arlo_all_std_csv.writerow(row_all_std)
            if pres_year:
                arlo_pres_avg_csv.writerow(row_pres_avg)
                arlo_pres_std_csv.writerow(row_pres_std)
            arlo_senate_avg_csv.writerow(row_senate_avg)
            arlo_senate_std_csv.writerow(row_senate_std)
            arlo_house_avg_csv.writerow(row_house_avg)
            arlo_house_std_csv.writerow(row_house_std)

            arlo_all_avg.flush()
            arlo_all_std.flush()
            if pres_year:
                arlo_pres_avg.flush()
                arlo_pres_std.flush()
            arlo_senate_avg.flush()
            arlo_senate_std.flush()
            arlo_house_avg.flush()
            arlo_house_std.flush()


def run_rla_poll_percent():
    for percent in [50, 75, 90]:
        percent_f = str(Decimal(percent) / Decimal(100))
        with open('arlo_results_poll_percent/arlo-ballot-poll-' + str(percent) + '-percent-all-' + str(
                risk_limit) + '.csv', 'w') as arlo_all, \
                open('arlo_results_poll_percent/arlo-ballot-poll-' + str(percent) + '-percent-pres-' + str(
                    risk_limit) + '.csv', 'w') as arlo_pres, \
                open('arlo_results_poll_percent/arlo-ballot-poll-' + str(percent) + '-percent-senate-' + str(
                    risk_limit) + '.csv', 'w') as arlo_senate, \
                open('arlo_results_poll_percent/arlo-ballot-poll-' + str(percent) + '-percent-house-' + str(
                    risk_limit) + '.csv', 'w') as arlo_house:
            all_indv_fieldnames = ['year', 'total'] + state_pos
            all_indv_fieldnames_dc = ['year', 'total'] + state_pos_dc
            arlo_all_csv = csv.DictWriter(arlo_all, fieldnames=all_indv_fieldnames_dc, restval=0)
            arlo_all_csv.writeheader()

            arlo_pres_csv = csv.DictWriter(arlo_pres, fieldnames=all_indv_fieldnames_dc, restval=0)
            arlo_pres_csv.writeheader()

            arlo_senate_csv = csv.DictWriter(arlo_senate, fieldnames=all_indv_fieldnames, restval=0)
            arlo_senate_csv.writeheader()

            arlo_house_csv = csv.DictWriter(arlo_house, fieldnames=all_indv_fieldnames, restval=0)
            arlo_house_csv.writeheader()

            for year in range(1976, 2020, 2):
                row_all = {'year': year}
                row_pres = {'year': year}
                row_senate = {'year': year}
                row_house = {'year': year}
                pres_year = year % 4 == 0
                all_total, pres_total, senate_total, house_total = 0, 0, 0, 0
                for state_po in state_pos_dc:
                    print(year, state_po)
                    if not pres_year and state_po == 'DC':
                        continue
                    election = elections[year][state_po]
                    assert pres_year == (election.pres is not None)
                    try:
                        sample = None
                        contest = None
                        if election.pres is None:
                            pres = None
                        else:
                            contest = election.pres
                            sample = bravo.get_sample_size(risk_limit, election.pres, None)
                            pres = get_sample_count(sample, percent_f)
                        if election.senate is None:
                            senate = None
                        else:
                            contest = election.senate
                            sample = bravo.get_sample_size(risk_limit, election.senate, None)
                            senate = get_sample_count(sample, percent_f)
                        house = 0
                        for contest in election.house.values():
                            contest = contest
                            sample = bravo.get_sample_size(risk_limit, contest, None)
                            house += get_sample_count(sample, percent_f)
                    except Exception as e:
                        print(e)
                        print(contest.name)
                        print(contest.candidates)
                        print(percent_f)
                        print(sample)
                        raise e

                    if 0 == house:
                        house = None

                    all_races = 0
                    if pres_year:
                        all_races += pres
                        pres_total += pres
                        row_pres[state_po] = pres
                    if senate is not None:
                        all_races += senate
                        senate_total += senate
                        row_senate[state_po] = senate
                    if house is not None:
                        all_races += house
                        house_total += house
                        row_house[state_po] = house

                    all_total += all_races
                    row_all[state_po] = all_races
                    row_all[state_po] = all_races

                row_all['total'] = math.ceil(np.average(all_total))
                if pres_year:
                    row_pres['total'] = math.ceil(np.average(pres_total))
                row_senate['total'] = math.ceil(np.average(senate_total))
                row_house['total'] = math.ceil(np.average(house_total))

                arlo_all_csv.writerow(row_all)
                if pres_year:
                    arlo_pres_csv.writerow(row_pres)
                arlo_senate_csv.writerow(row_senate)
                arlo_house_csv.writerow(row_house)

                arlo_all.flush()
                if pres_year:
                    arlo_pres.flush()
                arlo_senate.flush()
                arlo_house.flush()


# contest = elections[1984]['IN'].house[8]
# print(contest.candidates)
# sample = bravo.get_sample_size(risk_limit, contest, None)
# print(sample)
# print(sample['0.5'])

run_rla_poll_percent()