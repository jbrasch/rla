import csv
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt


def summarize(filename):

    expected = defaultdict(int)
    total = defaultdict(int)

    with open(filename) as votes_file:
        rows = csv.reader(votes_file)
        next(rows) # clear labels
        for row in rows:
            year = int(row[0])
            expected[year] += int(row[-1])
            total[year] += int(row[-3])


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

    ax.set_xlabel('Year')
    ax.set_ylabel('Expected Sample Size')
    ax.set_yticklabels([f'{int(tick)}%' for tick in ax.get_yticks()])
    ax.set_title('Ballot Comparison RLA')
    ax.legend()
    fig.savefig('figures/comp_rla.png')
    plt.close()


def year_data(filename, year):

    state_votes = defaultdict(int)
    with open(filename) as votes_file:
        rows = csv.reader(votes_file)
        next(rows) # clear labels
        for row in rows:
            if year == int(row[0]) and int(row[-3]) != 0:
                    state_votes[row[2]] += int(row[-1]) #/ int(row[-3]))

    return state_votes


def sort_votes(votes_dict):

    votes_list = list(votes_dict.items())
    votes_list.sort(key=lambda x: x[0])
    votes = [max(x[1],1) for x in votes_list]
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

    house_votes = year_data('house_comp_rla.csv', year)
    senate_votes = year_data('senate_comp_rla.csv', year)


    if year % 4 == 0:

        pres_votes = year_data('pres_comp_rla.csv', year)

        # fix senate
        for state in pres_votes.keys():
            if state not in senate_votes:
                senate_votes[state] = 0

        # fix house
        house_votes['DC'] = 0

        h_votes, states = sort_votes(house_votes)
        p_votes, _ = sort_votes(pres_votes)
        s_votes, _ = sort_votes(senate_votes)

        # burden(states, year, h_votes, s_votes, p_votes)

        h_votes = np.log10(h_votes)
        s_votes = np .log10(s_votes)
        p_votes = np.log10(p_votes)

        x = np.arange(len(states))
        w  = .2

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
        w  = .2

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
    ax.set_title(f'Ballot Comparison RLA - {year}')
    ax.legend()
    fig.savefig(f'figures/rla_{year}.png')
    plt.close()


def gen_figures():
    races = ('pres' , 'senate', 'house')#, 'pres-senate')
    filenames = (race + '_comp_rla.csv' for race in races)
    scatter(filenames, races)
    # [bar(year) for year in range(1976, 2020, 2)]

gen_figures()
