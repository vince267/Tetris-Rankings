import numpy as np
def elo_points(row):
    ctm_events = ['CTM Masters', 'CTM Challengers', 'CTM Futures', 'CTM Hopefuls']

    event_stage_points = {
        'CTWC': {'Finals': {'Win': 2000, 'Lose': 1200}, 'Semifinals': 800, 'Quarterfinals': 400,
            'Gold Round 2': 200, 'Gold Round 1': 100, 'Gold Round 0': 50},
        'CTM Mega Masters': {'Finals': {'Win': 2000, 'Lose': 1200}, 'Semifinals': 800, 'Quarterfinals': 400,
           'Round 2': 200, 'Round 1': 100, 'Round 0': 50},
        'CTM Lone Star': {'Finals': {'Win': 2000, 'Lose': 1200}, 'Semifinals': 600, 'Top 8': 200, 'Top 16': 50}
    }

    if row['Event'] in ctm_events:
        return 2 if row['Outcome'] == 'Win' else 1
    
    if row['Event'] in event_stage_points:
        stage_points = event_stage_points[row['Event']].get(row['Stage'])

        if isinstance(stage_points, dict):
            return stage_points.get(row['Outcome'], 0)
        return stage_points or 0
    
    return 0

def das_points(row):
    simple_bracket_events = ['CTM DAS Masters', 'CTM DAS World Circuit', 'CTM DAS Major Circuit', 'CTM DAS Super Circuit', 'CTM Lone Star DAS']

    event_stage_points = {
        'Jonas Cup': {'Finals': {'Win': 2000, 'Lose': 1200}, 'Semifinals': 800, 'Quarterfinals': 400,
            'Top 16': 200, 'Round 1': 100, 'Round 0': 50},
        'CTWC DAS': 
        {'2022': {'Finals': {'Win': 2000, 'Lose': 1200}, '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarterfinals': 400, 'Round of 16': 200, 'Round of 32': 100, 'Round of 48': 50},
        '2023': {'Finals': {'Win': 2000, 'Lose': 1200}, '3rd-place match': {'Win': 1000, 'Lose': 800}, 'Quarterfinals': 400, 
                 'Round of 16': 200, 'Round of 24': 150, 'Round of 32': 100, 'Round of 40': 75, 'Round of 48': 50},
        '2024': {'Grand Finals': {'Win': 2000, 'Lose': 1200}, 'Lower Bracket Final': 1000, 'Losers Round 8': 800,
            'Losers Round 7': 600, 'Losers Round 6': 400, 'Losers Round 5': 300, 'Losers Round 4': 200,
            'Losers Round 3': 150, 'Losers Round 2': 100, 'Losers Round 1': 75, 'Losers Round 0': 50}},
        'Lone Star DAS': {'Finals': {'Win': 1000, 'Lose': 600}, 'Semifinals': 300, 'Quarterfinals': 100, 'Round 1': 50},
        'CT DAS Minor': {'Finals': {'Win': 800, 'Lose': 500}, 'Semifinals': 200, 'Quarterfinals': 100, 'Round of 16': 50},
        'CT DAS': 
        {'2023': {'Finals': {'Win': 2000, 'Lose': 1200}, '3rd-place match': {'Win': 1000, 'Lose': 800}, 'Quarterfinals': 400,
            'Round of 16': 200, 'Round of 32': 100, 'Round of 64': 50}}
    }

    event = row.get('Event')
    if event in simple_bracket_events:
        return 2 if row['Outcome'] == 'Win' else 1
    
    edition = row.get('Edition')
    if event in event_stage_points:
        if edition in event_stage_points[event]:
            stage_points = event_stage_points[event][edition].get(row['Stage'])
        else:
            stage_points = event_stage_points[event].get(row['Stage'])

        if isinstance(stage_points, dict):
            return stage_points.get(row['Outcome'], 0)
        return stage_points or 0
    
    return 0


def ctdas_points(row):
    exception_events = {'CT DAS': '2022'}
    # year_to_year_events = ['CT DAS']

    event_stage_points = {
        'CT DAS Minor 2022': {'Finals': {'Win': 800, 'Lose': 500}, 'Semifinals': 200, 
                              'Quarterfinals': 100, 'Round of 16': 50},
        'CT DAS Minor 2023': {'Finals': {'Win': 800, 'Lose': 500}, 'Semifinals': 200, 
                              'Quarterfinals': 100, 'Round of 16': 50},
        'CT DAS Minor 2024': {'Finals': {'Win': 800, 'Lose': 500}, 'Semifinals': 200, 
                              'Quarterfinals': 100, 'Round of 16': 50},
        'CT DAS 2023': {'Finals': {'Win': 2000, 'Lose': 1200}, '3rd-place match': {'Win': 1000, 'Lose': 800}, 
                        'Quarterfinals': 400, 'Round of 16': 200, 'Round of 32': 100, 'Round of 64': 50}
    }

    event = row.get('Event')
    info = row.get('Info')
    # year = row.get('Edition')
    # if event in exception_events and year == exception_events[event]
    if event in exception_events and info == exception_events[event]:
        outcome = row['Outcome']
        return 2 if outcome == 'Win' else 1

    if event in event_stage_points:
        # if info in event_stage_points[event]:
        #     points_dict = event_stage_points[event][info]
        #     stage_points = points_dict.get(row['Stage'])
        #     if isinstance(stage_points, dict):
        #         return stage_points[row['Outcome']]
        #     return stage_points or 0 
        stage_points = event_stage_points[event].get(row['Info'])
        if isinstance(stage_points, dict):
            return stage_points[row['Outcome']]
        return stage_points or 0
    
        
    return 0


def get_stage(row):
    data = str(row['Info'])
    upper = data.upper()
    stage_tipoffs = ['ROUND', 'FINAL', 'TOP', 'MATCH']
    for stage in stage_tipoffs:
        if stage in upper:
            return data
    return row.get('Stage')

def get_edition(row):
    data = str(row['Info'])
    upper = data.upper()
    edition_tipoffs = ['20', 'SEASON', 'DIVISION', 'OVERDRIVE', 'ASCENSION', 'NOVEMBER']
    for edition in edition_tipoffs:
        if edition in upper:
            return data
    for i in range(6):
        if data == str(i):
            return data
    return row.get('Edition')

def split_edition(row):
    event = row.get('Event')
    if isinstance(event, str) and '20' in event:
        event = event.split()
        return event[-1]
    return row.get('Edition')

def modify_event(row):
    event = row.get('Event')
    if isinstance(event, str) and '20' in event:
        event = event.split()
        return " ".join(event[:-1])
    return row['Event']


def points_agg(points, event):
    simple_bracket_points = {
        'CTM Masters': {0: 0, 1: 100, 3: 200, 5: 400, 7: 800, 8: 1200},
        'CTM Challengers': {0: 0, 1: 25, 3: 50, 5: 100, 7: 200, 8: 400},
        'CTM Futures': {0: 0, 1: 10, 3: 20, 5: 30, 7: 50, 8: 100},
        'CTM Hopefuls': {0: 0, 1: 5, 3: 10, 5: 15, 7: 30, 8: 50},   
        'CTM DAS Masters': {0: 0, 1: 100, 3: 300, 5: 600, 7: 1000, 8: 1600},
        'CTM DAS World Circuit': {0: 0, 1: 50, 3: 10, 5: 200, 7: 400, 8: 800},
        'CTM DAS Major Circuit': {0: 0, 1: 25, 3: 50, 5: 100, 7: 200, 8: 400},
        'CTM DAS Super Circuit': {0: 0, 1: 10, 3: 20, 5: 40, 7: 100, 8: 200},
        'CTM Lone Star DAS': {0: 0, 1: 100, 3: 300, 5: 600, 7: 1000, 8: 1600}
    }

    # exception_events = {
    #     'CT DAS': 
    #     {'2022': {0: 0, 1: 50, 3: 100, 5: 200, 7: 400, 9: 800, 11: 1200, 12: 2000}}
    # }

    event_name = event.iloc[0]
    if event_name in simple_bracket_points:
        total_points = points.sum()
        return simple_bracket_points[event_name].get(total_points, 0)    
    # elif event_name in exception_events and year in exception_events[event_name]:
    #     total_points = points.sum()
    #     return exception_events[event_name][year].get(total_points, 0)
    else:
        return points.max()

def get_result(row):

    event_results = {
        'CTWC': {0: 'NA', 50: 'Qualified', 100: 'Top 32', 200: 'Top 16', 400: 'Top 8', 800: 'Top 4', 1200: '2nd place', 2000: 'Winner'},
        'Jonas Cup': {0: 'NA', 50: 'Qualified', 100: 'Top 32', 200: 'Top 16', 400: 'Top 8', 800: 'Top 4', 1200: '2nd place', 2000: 'Winner'},
        'CTM Mega Masters': {0: 'NA', 50: 'Qualified', 100: 'Top 32', 200: 'Top 16', 400: 'Top 8', 800: 'Top 4', 1200: '2nd place', 2000: 'Winner'},
        'CTM Lone Star': {0: 'NA', 50: 'Qualified', 200: 'Top 8', 600: 'Top 4', 1200: '2nd place', 2000: 'Winner'},
        'CTM Masters': {0: 'NA', 100: 'Qualified', 200: 'Top 8', 400: 'Top 4', 800: '2nd place', 1200: 'Winner'},
        'CTM Challengers': {0: 'NA', 25: 'Qualified', 50: 'Top 8', 100: 'Top 4', 200: '2nd place', 400: 'Winner'},
        'CTM Futures': {0: 'NA', 10: 'Qualified', 20: 'Top 8', 30: 'Top 4', 50: '2nd place', 100: 'Winner'},
        'CTM Hopefuls': {0: 'NA', 5: 'Qualified', 10: 'Top 8', 15: 'Top 4', 30: '2nd place', 50: 50},   
        'CTM DAS Masters': {0: 'NA', 100: 'Qualified', 300: 'Top 8', 600: 'Top 4', 1000: '2nd place', 1600: 'Winner'},
        'CTM DAS World Circuit': {0: 'NA', 50: 'Qualified', 10: 'Top 8', 200: 'Top 4', 400: '2nd place', 800: 'Winner'},
        'CTM DAS Major Circuit': {0: 'NA', 25: 'Qualified', 50: 'Top 8', 100: 'Top 4', 200: '2nd place', 400: 'Winner'},
        'CTM DAS Super Circuit': {0: 'NA', 10: 'Qualified', 20: 'Top 8', 40: 'Top 4', 100: '2nd place', 200: 'Winner'},
        'CTM Lone Star DAS': {0: 'NA', 100: 'Qualified', 300: 'Top 8', 600: 'Top 4', 1000: '2nd place', 1600: 'Winner'},
        'Lone Star DAS': {0: 'NA', 50: 'Qualified', 100: 'Top 8', 300: 'Top 4', 600: '2nd place', 1000: 'Winner'},
        'CTWC DAS': {'2022': {0: 'NA', 50: 'Qualified', 100: 'Top 32', 200: 'Top 16', 400: 'Top 8', 
                              800: '4th place', 1000: '3rd place', 1200: '2nd place', 2000: 'Winner'},
                     '2023': {0: 'NA', 50: 'Qualified', 75: 'Top 40', 100: 'Top 32', 150: 'Top 24', 200: 'Top 16', 
                              400: 'Top 8', 800: '4th place', 1000: '3rd place', 1200: '2nd place', 2000: 'Winner'},
                     '2024': {0: 'NA', 50: 'Qualified', 75: 'Top 40', 100: 'Top 32', 150: 'Top 24', 200: 'Top 16', 300: 'Top 12', 
                              400: 'Top 8', 600: 'Top 6', 800: '4th place', 1000: '3rd place', 1200: '2nd place', 2000: 'Winner'}},
        'CT DAS Minor': {0: 'NA', 50: 'Qualified', 100: 'Top 8', 200: 'Top 4', 500: '2nd place', 800: 'Winner'},
        'CT DAS': {0: 'NA', 50: 'Qualified', 100: 'Top 32', 200: 'Top 16', 400: 'Top 8', 800: 'Top 4', 1000: '3rd place', 1200: '2nd place', 2000: 'Winner'},
    }


    event_name = row.get('Event')
    if event_name in event_results:
        points = row.get('Event_Points')
        edition = row.get('Edition')
        if edition in event_results[event_name]:
            return event_results[event_name][edition].get(points, 'ERROR')
        return event_results[event_name].get(points, 'ERROR')    
    else:
        return "NA"


def ctdas_points_agg(points, edition):
    exception_years = {
        '2022': {0: 0, 1: 50, 3: 100, 5: 200, 7: 400, 9: 800, 11: 1200, 12: 2000}   
    }

    year = edition.iloc[0]
    if year in exception_years:
        total_points = points.sum()
        return exception_years[year].get(total_points, 0)    
    # if event_name in exception_events and year in exception_events[event_name]:
    #     total_points = points.sum()
    #     return exception_events[event_name][year].get(total_points, 0)
    else:
        return points.max()

def top_performances(list, n):
    return sum(sorted(list, reverse=True)[:n])


