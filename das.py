import pandas as pd
from datetime import datetime, timedelta
from pandasql import sqldf
pd.set_option('display.max_rows', None)

# Filter data for only the prior n years
num_years = 5

# Count the top n performances in the given timeframe
num_performances = 10

# Print top n players
num_top_players = 20

# Decide whether to drop friendlies or include them
drop_friendlies = True

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

    event_stage_points = {
        'Jonas Cup': {
            'Final': {'Win': 2000, 'Lose': 1200},
            'Semi-final': 800,
            'Quarter-final': 400,
            'Top 16': 200,
            'Round 1': 100,
            'Round 0': 50
        },
        'CTWC DAS': 
        {
        '2022': {
            'Final': {'Win': 2000, 'Lose': 1200},
            '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarter-final': 400,
            'Round of 16': 200,
            'Round of 32': 100,
            'Round of 48': 50
        },
        '2023': {
            'Final': {'Win': 2000, 'Lose': 1200},
            '3rd-place match': {'Win': 1000, 'Lose': 800},
            'Quarter-final': 400,
            'Round of 16': 200,
            'Round of 24': 150,
            'Round of 32': 100,
            'Round of 40': 75,
            'Round of 48': 50
        },
        '2024': {
            'Grand Final': {'Win': 2000, 'Lose': 1200},
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
            'Final': {'Win': 1000, 'Lose': 600},
            'Semi-final': 300,
            'Quarter-final': 100,
            'Round 1': 50,
        }
    }

    event = row.get('Event')
    edition = row.get('Edition')
    if event == 'CTWC DAS':
        points_dict = event_stage_points[event][edition]
        stage_points = points_dict.get(row['Stage'])
        if isinstance(stage_points, dict):
            return stage_points[row['Outcome']]
        return stage_points or 0

    elif event in event_stage_points:
        stage_points = event_stage_points[event].get(row['Stage'])
        if isinstance(stage_points, dict):
            return stage_points[row['Outcome']]
        return stage_points or 0
    
    elif event in simple_bracket_events or (event in exception_events and edition == exception_events[event]):
        outcome = row['Outcome']
        return 2 if outcome == 'Win' else 1
        
    return 0

def points_agg(points, event):
    # CT DAS Minor is also a 16 person bracket, but has bo3(bo3) format until bo5(bo3) in the finals 
    simple_bracket_points = {
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
        },
        'CT DAS': {
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

    event_name = event.iloc[0]
    if event_name in simple_bracket_points:
        total_points = points.sum()
        return simple_bracket_points[event_name].get(total_points, 0)
    else:
        return points.max()

def top_performances(list, n):
    return sum(sorted(list, reverse=True)[:n])


# Google sheets CSV export URL format
sheet_id = "1nEN0MAbueG36UDkpfUsPZEmAMuKif6IcLAmJ8iZhCe8"
gid = "805197322"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Read specified columns into a dataframe
cols = range(1,9)
df = pd.read_csv(url, usecols=cols)

# Drop blank column and rename columns
df = df.drop(['Unnamed: 5'], axis=1)
df = df.rename(columns={'Player1': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Player2': 'Loser', 'Edition/Round': 'Info', 'Date/Time (UTC)': 'Date'})

# Fill null event entries
df['Event'] = df['Event'].fillna("NA")

df['Event'] = df['Event'].str.replace('Das', 'DAS')

# Drop friendly events
if drop_friendlies:
    drop_list = ['Friendlies', 'Friendlies: Retribution', 'Friendlies: Rivals', 'LATAM Friendlies', 'LYMYMI Tournament', 'Tetris Friendlies', 'TNP']
    df = df[~df['Event'].isin(drop_list)]


# Move the winners to column 1
switch = df['Wins'] < df['Losses']
df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values

# Convert dates to datetime format
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S')

# Replace null values for Event column
df['Event'] = df['Event'].fillna('None')

# Filter data to the given time frame
time_frame = datetime.now() - timedelta(days = num_years * 365 + 1)
df = df[df['Date'] >= time_frame]

# Separate Date column into date and time columns
df['Time'] = df['Date'].dt.time
df['Date'] = df['Date'].dt.date

ct_das_df = df[df['Event'].str.contains('CT DAS')]

switch = ct_das_df['Winner'] > ct_das_df['Loser']
ct_das_df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = ct_das_df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values

print(ct_das_df.groupby(['Winner', 'Loser', 'Event', 'Info', 'Date']))
print(ct_das_df.groupby('Event').count())


# Drop duplicate rows
df = df.drop_duplicates(['Winner', 'Wins', 'Losses', 'Loser', 'Event', 'Info', 'Date', 'Time'])



# Reshape dataframe
winners_df = df[['Winner', 'Event', 'Info', 'Date', 'Time']].rename(columns={'Winner': 'Player'})
winners_df['Outcome'] = 'Win'
losers_df = df[['Loser', 'Event', 'Info', 'Date', 'Time']].rename(columns={'Loser': 'Player'})
losers_df['Outcome'] = 'Lose'
df = pd.concat([winners_df, losers_df])

# Split Info column into an edition column and a stage column. Original Info column was not consistent. 
df['Stage'] = df.apply(get_stage, axis=1)
df['Edition'] = df.apply(get_edition, axis=1)

# For events with the edition in the event name, move the edition to the edition column
df['Edition'] = df.apply(split_edition, axis=1).fillna('NA')
df['Event'] = df.apply(modify_event, axis=1).fillna('NA')


# Reorder columns, drop Info column
df = df[['Player', 'Event', 'Edition', 'Stage', 'Outcome', 'Date', 'Time']]

# Enter initial point values for each match at notable events
df['Points'] = 0
df['Points'] = df.apply(das_points, axis=1)


# Create players dataframe
# Columns: Player, Wins, Losses, Total_Points (to come later)
players_df = df.groupby(['Player', 'Outcome']).size().unstack(fill_value=0)
players_df = players_df.rename(columns={'Win': 'Wins', 'Lose': 'Losses'})
players_df = players_df.rename_axis(None, axis=1).reset_index()
players_df = players_df[['Player', 'Wins', 'Losses']]

# Make an event results dataframe
# Columns: Player, Event, Edition, Type, Result

event_results_df = df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: points_agg(points, df.loc[points.index, 'Event']))
)

# Add Total Points column to dataframe
player_points = event_results_df.groupby('Player')['Event_Points'].agg(top_performances, num_performances)
players_df['Total_Points'] = players_df['Player'].map(player_points)
players_df['Total_Points'] = players_df['Total_Points'].fillna(0)
players_df['Total_Points'] = players_df['Total_Points'].astype(int)
players_df = players_df.sort_values(by='Total_Points', ascending=False).reset_index(drop=True)
players_df.index += 1

print(players_df.head(20))

player = "SHARKY"
best_results = event_results_df.loc[event_results_df['Player'] == player]
best_results = best_results.sort_values(by='Event_Points', ascending=False)

# print(best_results.head(15))


# df = df.sort_values(by='Points')
# print(df.tail(100))

# print(event_results_df.loc[event_results_df['Player'] == 'SHARKY'])
# print(df.loc[df['Player'] == 'SHARKY'])

# df = df.sort_values(by='Event')
# print(df.tail())
# for x in (sorted(df['Event'].unique())):
#     print(x)

# print(df.loc[(df['Event'] == 'Lone Star Das'), ['Edition', 'Stage']])

# print(df.loc[(df['Event'] == 'CTM Lone Star DAS'), ['Edition', 'Stage']])


# execute = lambda q: sqldf(q, globals())
# query = "SELECT * FROM df WHERE Event LIKE '%CT DAS%' ORDER BY Date"
# query_df = execute(query)
# print(query_df)

# print(df.info())
