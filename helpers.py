def elo_points(row):
    ctm_events = ['CTM Masters', 'CTM Challengers', 'CTM Futures', 'CTM Hopefuls']

    event_stage_points = {
        'CTWC': {
            'Finals': {'Win': 2000, 'Lose': 1200},
            'Semifinals': 800,
            'Quarterfinals': 400,
            'Gold Round 2': 200,
            'Gold Round 1': 100,
            'Gold Round 0': 50
        },
        'CTM Mega Masters': {
           'Finals': {'Win': 2000, 'Lose': 1200},
           'Semifinals': 800,
           'Quarterfinals': 400,
           'Round 2': 200,
           'Round 1': 100,
           'Round 0': 50 
        },
        'CTM Lone Star': {
            'Finals': {'Win': 2000, 'Lose': 1200},
            'Semifinals': 600,
            'Top 8': 200,
            'Top 16': 50
        }
    }

    if row['Event'] in ctm_events:
        return 2 if row['Outcome'] == 'Win' else 1
    
    if row['Event'] in event_stage_points:
        stage_points = event_stage_points[row['Event']].get(row['Stage'])

        if isinstance(stage_points, dict):
            return stage_points.get(row['Outcome'], 0)
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
    if '20' in row['Event']:
        event = row['Event'].split()
        n = len(event)
        return event[-1]
    return row['Edition']

def modify_event(row):
    if '20' in row['Event']:
        event = row['Event'].split()
        n = len(event)
        return " ".join(event[:-1])
    return row['Event']

def das_points(row):
    simple_bracket_events = ['CTM DAS Masters', 'CTM DAS World Circuit', 'CTM DAS Major Circuit', 'CTM DAS Super Circuit', 'CTM Lone Star DAS']
    exception_events = {'CT DAS': '2022'}
    year_to_year_events = ['CTWC DAS', 'CT DAS']

    event_stage_points = {
        'Jonas Cup': {
            'Finals': {'Win': 2000, 'Lose': 1200},
            'Semifinals': 800,
            'Quarterfinals': 400,
            'Top 16': 200,
            'Round 1': 100,
            'Round 0': 50
        },
        'CTWC DAS': 
        {
        '2022': {
            'Finals': {'Win': 2000, 'Lose': 1200},
            '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarterfinals': 400,
            'Round of 16': 200,
            'Round of 32': 100,
            'Round of 48': 50
        },
        '2023': {
            'Finals': {'Win': 2000, 'Lose': 1200},
            '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarterfinals': 400,
            'Round of 16': 200,
            'Round of 24': 150,
            'Round of 32': 100,
            'Round of 40': 75,
            'Round of 48': 50
        },
        '2024': {
            'Grand Finals': {'Win': 2000, 'Lose': 1200},
            'Lower Bracket Final': 1000,
            'Losers Round 8': 800,
            'Losers Round 7': 600,
            'Losers Round 6': 400,
            'Losers Round 5': 300,
            'Losers Round 4': 200,
            'Losers Round 3': 150,
            'Losers Round 2': 100,
            'Losers Round 1': 75,
            'Losers Round 0': 50
        }
        },
        'Lone Star DAS': {
            'Finals': {'Win': 1000, 'Lose': 600},
            'Semifinals': 300,
            'Quarterfinals': 100,
            'Round 1': 50,
        },
        'CT DAS Minor': {
            'Finals': {'Win': 600, 'Lose': 400},
            'Semifinals': 200,
            'Quarterfinals': 100,
            'Round of 16': 50,
        },
        'CT DAS': 
        {
        '2023': {
            'Finals': {'Win': 2000, 'Lose': 1200},
            '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarterfinals': 400,
            'Round of 16': 200,
            'Round of 32': 100,
            'Round of 64': 50
        }
        }
    }

def ctdas_points(row):
    exception_events = {'CT DAS': '2022'}
    # year_to_year_events = ['CT DAS']

    event_stage_points = {
        'CT DAS Minor 2022': {
            'Finals': {'Win': 800, 'Lose': 500},
            'Semifinals': 200,
            'Quarterfinals': 100,
            'Round of 16': 50,
        },
        'CT DAS Minor 2023': {
            'Finals': {'Win': 800, 'Lose': 500},
            'Semifinals': 200,
            'Quarterfinals': 100,
            'Round of 16': 50,
        },
        'CT DAS Minor 2024': {
            'Finals': {'Win': 800, 'Lose': 500},
            'Semifinals': 200,
            'Quarterfinals': 100,
            'Round of 16': 50,
        },
        'CT DAS 2023': 
        {
            'Finals': {'Win': 2000, 'Lose': 1200},
            '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarterfinals': 400,
            'Round of 16': 200,
            'Round of 32': 100,
            'Round of 64': 50
        }
    }

    event = row.get('Event')
    info = row.get('Info')

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

def points_agg(points, event):
    # CT DAS Minor is also a 16 person bracket, but has bo3(bo3) format until bo5(bo3) in the finals 
    simple_bracket_points = {
        'CTM Masters': {
            0: 0,
            1: 100,
            3: 200,
            5: 400,
            7: 800,
            8: 1200
            },
        'CTM Challengers': {
            0: 0,
            1: 25,
            3: 50,
            5: 100,
            7: 200,
            8: 400
        },
        'CTM Futures': {
            0: 0,
            1: 10,
            3: 20,
            5: 30,
            7: 50,
            8: 100
        },
        'CTM Hopefuls': {
            0: 0,
            1: 5,
            3: 10,
            5: 15,
            7: 30, 
            8: 50
        },   
        'CTM DAS Masters': {
            0: 0,
            1: 100,
            3: 300,
            5: 600,
            7: 1000,
            8: 1600
            },
        'CTM DAS World Circuit': {
            0: 0,
            1: 50,
            3: 10,
            5: 200,
            7: 400,
            8: 800
        },
        'CTM DAS Major Circuit': {
            0: 0,
            1: 25,
            3: 50,
            5: 100,
            7: 200,
            8: 400
        },
        'CTM DAS Super Circuit': {
            0: 0,
            1: 10,
            3: 20,
            5: 40,
            7: 100,
            8: 200
        },
        'CTM Lone Star DAS': {
            0: 0,
            1: 100,
            3: 300,
            5: 600,
            7: 1000,
            8: 1600
        }
    }

    # exception_events = {
    #     'CT DAS': 
    #     {'2022': {
    #         0: 0,
    #         1: 50,
    #         3: 100,
    #         5: 200,
    #         7: 400,
    #         9: 800,
    #         11: 1200,
    #         12: 2000
    #     }}
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

def points_agg(points, event):
    ctm_points = {
        'CTM Masters': {
            0: 0,
            1: 100,
            3: 200,
            5: 400,
            7: 800,
            8: 1200
            },
        'CTM Challengers': {
            0: 0,
            1: 25,
            3: 50,
            5: 100,
            7: 200,
            8: 400
        },
        'CTM Futures': {
            0: 0,
            1: 10,
            3: 20,
            5: 30,
            7: 50,
            8: 100
        },
        'CTM Hopefuls': {
            0: 0,
            1: 5,
            3: 10,
            5: 15,
            7: 30, 
            8: 50
        }   
    }
    event_name = event.iloc[0]
    if event_name in ctm_points:
        total_points = points.sum()
        return ctm_points[event_name].get(total_points, 0)
    else: 
        return points.max()


def ctdas_points_agg(points, edition):
    exception_years = {
        '2022': {
            0: 0,
            1: 50,
            3: 100,
            5: 200,
            7: 400,
            9: 800,
            11: 1200,
            12: 2000
        }
    }

    year = edition.iloc[0]
    if year in exception_years:
        total_points = points.sum()
        return exception_years[year].get(total_points, 0)    
    # elif event_name in exception_events and year in exception_events[event_name]:
    #     total_points = points.sum()
    #     return exception_events[event_name][year].get(total_points, 0)
    else:
        return points.max()

def top_performances(list, n):
    return sum(sorted(list, reverse=True)[:n])
