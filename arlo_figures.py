import csv
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

from construct_contests import elections


def summarize(filename):
    expected = defaultdict(int)
    total = defaultdict(int)

    with open(filename) as votes_file:
        rows = csv.DictReader(votes_file)
        for row in rows:
            year = int(row['year'])
            expected[year] = int(row['total'])
            for state in row.keys():
                if state in elections[year]:
                    total[year] += elections[year][state].total_votes()

    ratio = [ex / t * 100 for ex, t in zip(expected.values(), total.values())]
    return list(total), ratio


def scatter(filenames, races):
    fig, ax = plt.subplots()

    for filename, race in zip(filenames, races):
        years, ratios = summarize(filename)
        ax.scatter(years, ratios, label=race)
        # linear regresssion
        m, b = np.polyfit(years, ratios, 1)
        plt.plot(years, [m * i + b for i in years])

    plt.ylim([0, 12])
    ax.set_yticklabels
    ax.set_xlabel('Year')
    ax.set_ylabel('Expected Sample Size')
    ax.set_yticklabels([f'{int(tick)}%' for tick in ax.get_yticks()])
    ax.set_title('Ballot Polling RLA')
    ax.legend()
    fig.savefig('arlo_figures/poll_rla.png')
    plt.close()


def year_data(filename, year):
    with open(filename) as votes_file:
        rows = csv.DictReader(votes_file)
        for row in rows:
            if year == int(row['year']):
                return row
    return None


def sort_votes(votes_dict):
    votes_dict.pop('DC', None)
    votes_dict.pop('year', None)
    votes_dict.pop('total', None)
    votes_list = list(votes_dict.items())
    votes_list.sort(key=lambda x: x[0])
    votes = [max(int(x[1]), 1) for x in votes_list]
    states = [x[0] for x in votes_list]
    return votes, states


# def burden(states, year, h_votes, s_votes, p_votes=[]):

#     fig, ax = plt.subplots(figsize=(20, 6))

#     total = sum(h_votes) + sum(s_votes) + sum(p_votes)

#     if len(p_votes) != 0:
#         burden = [(h + s + p) / total for h, s, p in zip(h_votes, s_votes, p_votes)]
#     else:
#         burden = [(h + s) / total * 100 for h, s in zip(h_votes, s_votes)]
#     ax.bar(states, burden)

#     # ax.set_xlabel('Year')
#     ax.set_ylabel('$log_10$ Burden')
#     ax.set_title(f'Ballot Comparison RLA - {year}')
#     # ax.legend()
#     fig.savefig(f'figures/burden_{year}.png')


def bar(year):
    fig, ax = plt.subplots(figsize=(20, 6))

    house_votes = year_data('arlo_results_poll_sim/batch/arlo-ballot-poll-house-10-avg.csv', year)
    senate_votes = year_data('arlo_results_poll_sim/batch/arlo-ballot-poll-senate-10-avg.csv', year)

    if year % 4 == 0:

        pres_votes = year_data('arlo_results_poll_sim/batch/arlo-ballot-poll-pres-10-avg.csv', year)

        # fix senate
        for state in pres_votes.keys():
            if state not in senate_votes:
                senate_votes[state] = 0

        h_votes, states = sort_votes(house_votes)
        p_votes, _ = sort_votes(pres_votes)
        s_votes, _ = sort_votes(senate_votes)

        # burden(states, year, h_votes, s_votes, p_votes)

        h_votes = np.log10(h_votes)
        s_votes = np.log10(s_votes)
        p_votes = np.log10(p_votes)

        x = np.arange(len(states))
        w = .2

        ax.bar(x, h_votes, w, label='house', color='red')
        ax.bar(x + w, s_votes, w, label='senate', color='blue')
        ax.bar(x + 2 * w, p_votes, w, label='president', color='green')

        ax.axhline(h_votes.mean(), linestyle='dashed', color='lightcoral')
        ax.axhline(s_votes.mean(), linestyle='dashed', color='skyblue')
        ax.axhline(p_votes.mean(), linestyle='dashed', color='lightgreen')

        ax.set_xticks(x)
        ax.set_xticklabels(states)

    else:
        # fix senate
        for state in house_votes.keys():
            if state not in senate_votes:
                senate_votes[state] = 0

        h_votes, states = sort_votes(house_votes)
        s_votes, _ = sort_votes(senate_votes)

        # burden(states, year, h_votes, s_votes)

        h_votes = np.log10(h_votes)
        s_votes = np.log10(s_votes)

        x = np.arange(len(states))
        w = .2

        ax.bar(x, h_votes, w, label='house', color='red')
        ax.bar(x + w, s_votes, w, label='senate', color='blue')
        # ax.bar(x + 2 * w, p_votes, w, label='president', color='green')

        ax.axhline(h_votes.mean(), linestyle='dashed', color='lightcoral')
        ax.axhline(s_votes.mean(), linestyle='dashed', color='skyblue')
        # ax.axhline(p_votes.mean(), linestyle='dashed', color='lightgreen')

        ax.set_xticks(x)
        ax.set_xticklabels(states)

    # ax.set_xlabel('Year')
    ax.set_ylabel('$log_{10}$ Expected Ballots Sampled')
    ax.set_yticklabels([f'$10^{int(tick)}$' for tick in ax.get_yticks()])
    ax.set_title(f'Ballot Polling RLA - {year}')
    ax.legend()
    fig.savefig(f'arlo_figures/rla_{year}.png')
    plt.close()


def gen_figures():
    races = ('President', 'Senate', 'House')  # , 'pres-senate')
    filenames = ['arlo_results_poll_sim/batch/arlo-ballot-poll-pres-10-avg.csv',
                 'arlo_results_poll_sim/batch/arlo-ballot-poll-senate-10-avg.csv',
                 'arlo_results_poll_sim/batch/arlo-ballot-poll-house-10-avg.csv']
    scatter(filenames, races)


# gen_figures()
# bar(2016)
# bar(2018)
# with open('arlo_results_poll_sim/batch/arlo-ballot-poll-pres-10-avg.csv') as pres_f, \
#         open('arlo_results_poll_sim/batch/arlo-ballot-poll-senate-10-avg.csv') as senate_f, \
#         open('arlo_results_poll_sim/batch/arlo-ballot-poll-house-10-avg.csv') as house_f, \
#         open('arlo_results_poll_sim/batch/arlo-ballot-poll-all-10-avg.csv') as all_f, \
#         open('poll_rla.csv', 'w') as results_f:
#     house_csv = csv.DictReader(house_f)
#     senate_csv = csv.DictReader(senate_f)
#     pres_csv = csv.DictReader(pres_f)
#     all_csv = csv.DictReader(all_f)
#     results = {}
#     for row in house_csv:
#         results[row['year']] = {}
#         results[row['year']]['Year'] = row['year']
#         results[row['year']]['House'] = "{:,}".format(int(row['total']))
#     for row in senate_csv:
#         results[row['year']]['Senate'] = "{:,}".format(int(row['total']))
#     for row in pres_csv:
#         results[row['year']]['President'] = "{:,}".format(int(row['total']))
#     for row in all_csv:
#         results[row['year']]['All'] = "{:,}".format(int(row['total']))
#
#     results_csv = csv.DictWriter(results_f, fieldnames=['Year', 'House', 'Senate', 'President', 'All'])
#     results_csv.writeheader()
#     for year in range(1976, 2020, 2):
#         result =results[str(year)]
#         results_csv.writerow(result)


with open('poll_rla_with_cost.csv') as poll_f, \
        open('comp_rla.csv') as comp_f, \
        open('comp_vs_poll_rla_comma.csv', 'w') as results_f:
    poll_csv = csv.DictReader(poll_f)
    comp_csv = csv.DictReader(comp_f)
    results = {}
    for row in poll_csv:
        results[row['Year']] = {}
        results[row['Year']]['Year'] = row['Year']
        results[row['Year']]['Ballot-Polling'] = row['Total']
    for row in comp_csv:
        results[row['Year']]['Ballot-Comparison'] = row['Total']

    results_csv = csv.DictWriter(results_f, fieldnames=['Year', 'Ballot-Comparison', 'Ballot-Polling', 'Percent'],delimiter=';')
    results_csv.writeheader()
    average_percent = 0
    n = 0
    for year in range(1976, 2020, 2):
        result = results[str(year)]
        poll = int(result['Ballot-Polling'])
        comp = int(result['Ballot-Comparison'])
        result['Ballot-Polling'] = "{:,}".format(poll)
        result['Ballot-Comparison'] = "{:,}".format(comp)
        diff = poll - comp
        p = diff / comp * 100
        average_percent += p
        n += 1
        percent_increase = str(round(diff / comp * 100, 1)) + ' \%'
        # result['Difference'] = diff
        result['Percent'] = percent_increase
        results_csv.writerow(result)
    print(average_percent / n)

# with open('house_comp_rla.csv') as house_comp, open('pres')


# with open('state_comp_rla.csv') as state_totals_f:
#     state_totals_csv = csv.DictReader(state_totals_f)
#     state_totals_2016 = {}
#     total_2016 = 6312790
#     for row in state_totals_csv:
#         if row['year'] == str(2016):
#             # print(row)
#             state_totals_2016[row['state']] = row
#     outlier_total = int(state_totals_2016['CA']['pres & sen & house']) + int(state_totals_2016['MI']['pres & sen & house']) + int(state_totals_2016['NH']['pres & sen & house'])
#     print('CA', state_totals_2016['CA']['pres & sen & house'])
#     print('MI', state_totals_2016['MI']['pres & sen & house'])
#     print('NH', state_totals_2016['NH']['pres & sen & house'])
#     print('WI', state_totals_2016['WI']['pres & sen & house'])
#     print('PA', state_totals_2016['PA']['pres & sen & house'])
#     print(outlier_total / total_2016)

# with open('arlo_results_poll_sim/batch/arlo-ballot-poll-all-10-avg.csv') as all_f:
#     state_totals_csv = csv.DictReader(all_f)
#     state_totals_2016 = {}
#     for row in state_totals_csv:
#         if row['year'] == str(2016):
#             state_totals_2016 = row
#             break
#     outlier_total = int(state_totals_2016['CA']) + int(state_totals_2016['MI']) + int(state_totals_2016['NH'])
#     print('CA', state_totals_2016['CA'])
#     print('MI', state_totals_2016['MI'])
#     print('NH', state_totals_2016['NH'])
#     print('WI', state_totals_2016['WI'])
#     print('PA', state_totals_2016['PA'])
#     print(outlier_total / int(state_totals_2016['total']))

with open('poll_rla_with_cost.csv') as input, open('poll_rla.csv', 'w') as output:
    in_csv = csv.DictReader(input)
    out_csv = csv.DictWriter(output, fieldnames=in_csv.fieldnames, delimiter=';')
    out_csv.writeheader()
    adjusted_headers = in_csv.fieldnames[1:5]
    adjusted_costs = in_csv.fieldnames[5:]
    for row in in_csv:
        result = {'Year': row['Year']}
        for h in adjusted_headers:
            if '' != row[h]:
                result[h] = "{:,}".format(int(row[h]))
        for h in adjusted_costs:
            if '' != row[h]:
                result[h] = '\$' + "{:,}".format(int(row[h]))
        out_csv.writerow(result)

with open('comp_rla.csv') as input, open('comp_rla_comma.csv', 'w') as output:
    in_csv = csv.DictReader(input)
    out_csv = csv.DictWriter(output, fieldnames=in_csv.fieldnames, delimiter=';')
    out_csv.writeheader()
    adjusted_headers = in_csv.fieldnames[1:6]
    adjusted_costs = in_csv.fieldnames[6:]
    for row in in_csv:
        result = {'Year': row['Year']}
        for h in adjusted_headers:
            if '' != row[h]:
                result[h] = "{:,}".format(int(row[h]))
        for h in adjusted_costs:
            if '' != row[h]:
                result[h] = '\$' + "{:,}".format(int(row[h]))
        out_csv.writerow(result)

# with open('comp_vs_poll_rla.csv') as input, open('comp_vs_poll_rla_comma.csv', 'w') as output:
#     in_csv = csv.DictReader(input)
#     out_csv = csv.DictWriter(output, fieldnames=in_csv.fieldnames, delimiter=';')
#     out_csv.writeheader()
#     adjusted_headers = in_csv.fieldnames[1:6]
#     adjusted_costs = in_csv.fieldnames[6:]
#     for row in in_csv:
#         result = {'Year': row['Year']}
#         for h in adjusted_headers:
#             if '' != row[h]:
#                 result[h] = "{:,}".format(int(row[h]))
#         for h in adjusted_costs:
#             if '' != row[h]:
#                 result[h] = '\$' + "{:,}".format(int(row[h]))
#         out_csv.writerow(result)
