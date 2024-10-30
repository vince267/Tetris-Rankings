import pandas as pd
from pandasql import sqldf
from datetime import datetime, timedelta

# Filter data for only the prior n years
num_years = 2 

# Count the top n performances in the given timeframe
num_performances = 10

# Print top n players
num_top_players = 20

# Filter data for events of type Elo, Das, or Friendly.
match_type = 'ELO'
possible_types = ['ELO', 'DAS', 'FRIENDLY']


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

def top_performances(list, n):
    return sum(sorted(list, reverse=True)[:n])


# Google Sheets CSV export URL format
sheet_id = "1Rw1XT90YD8HvYN4JS0Ba1tgkp7UlrG4ksPuP4Yc4SNM"
gid = "658545272"

das_sheet_id = "1nEN0MAbueG36UDkpfUsPZEmAMuKif6IcLAmJ8iZhCe8"
das_gid = "805197322"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Read the data into a DataFrame
cols = range(0,12)
df = pd.read_csv(url, usecols=cols)

# Rename columns and drop space buffer column.
df = df.rename(columns={'Result': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Unnamed: 4': 'Loser', 'Date/time': 'Date', 'Round/game': 'Stage', 'Restreamer/location': 'Location'})
df.drop(['Unnamed: 5'], axis = 1, inplace = True) 

# Filter dataframe to only of specified match type
if match_type in possible_types:
    df = df[df['Type'] == match_type]

# Some rows have wins < losses. Normalize rows so that the winner is always on the left.
switch = df['Wins'] < df['Losses']
df.loc[switch, ['Winner', 'Loser', 'Wins', 'Losses']] = df.loc[switch, ['Loser', 'Winner', 'Losses', 'Wins']].values 

# Convert dates to datetime
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S')

# Filter rows with dates within the last n years
time_frame = datetime.now() - timedelta(days= num_years * 365 + 1)
df = df[df['Date'] >= time_frame]

# Reshape dataframe 
winners_df = df[['Match', 'Winner', 'Event', 'Edition', 'Date', 'Stage', 'Location', 'Type']].rename(columns={'Winner': 'Player'})
winners_df['Outcome'] = 'Win'
losers_df = df[['Match', 'Loser', 'Event', 'Edition', 'Date', 'Stage', 'Location', 'Type']].rename(columns={'Loser': 'Player'})
losers_df['Outcome'] = 'Lose'
df = pd.concat([winners_df, losers_df])

# Enter initial point values for each match at notable events
df['Points'] = 0
df['Points'] = df.apply(elo_points, axis=1)




# Make an event results dataframe
# Columns: Player, Event, Edition, Type, Result

event_results_df = df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: points_agg(points, df.loc[points.index, 'Event']))
)

# Create players dataframe
# Columns: Player, Wins, Losses, Total Points (to come later)
players_df = df.groupby(['Player', 'Outcome']).size().unstack(fill_value=0)
players_df = players_df.rename(columns={'Win': 'Wins', 'Lose': 'Losses'})
players_df = players_df.rename_axis(None, axis=1).reset_index()
players_df = players_df[['Player', 'Wins', 'Losses']]

# Add Total Points column to players dataframe
player_points = event_results_df.groupby('Player')['Event_Points'].agg(top_performances, num_performances)
players_df['Total_Points'] = players_df['Player'].map(player_points)
players_df['Total_Points'] = players_df['Total_Points'].fillna(0)
players_df['Total_Points'] = players_df['Total_Points'].astype(int)
players_df = players_df.sort_values(by='Total_Points', ascending=False).reset_index(drop=True)
players_df.index += 1
# players_df = players_df.sort_values(by='Total_Points')

pd.set_option('display.max_rows', None)

print(players_df.head(num_top_players))


player = "SHARKY"
best_results = event_results_df.loc[event_results_df['Player'] == player]
best_results = best_results.sort_values(by='Event_Points', ascending=False)

# Uncomment to print best results for given player
# print(best_results.head(15))


# Uncomment for sql style queries
# execute = lambda q: sqldf(q, globals())
# query = "SELECT DISTINCT(Event) FROM df ORDER BY Event"
# query_df = execute(query)
# print(query_df)

