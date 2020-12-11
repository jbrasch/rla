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


gen_figures()
# bar(2016)
# bar(2018)
