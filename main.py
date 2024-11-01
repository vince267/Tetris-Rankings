import pandas as pd
from pandasql import sqldf
from datetime import datetime, timedelta
from helpers import elo_points, points_agg, get_result, top_performances

# Filter data for only the prior n years
num_years = 2 

# Count the top n performances in the given timeframe
num_performances = 10

# Print top n players
num_top_players = 20

# Filter data for events of type Elo or Friendly. Friendly only gives win loss records. 
# Set match type to 'ANY' (or any string other than ELO or FRIENDLY) to include friendlies in win-loss record.
match_type = 'ELO'
possible_types = ['ELO', 'FRIENDLY']

# Modify player name to access summary of other players.
player = 'fractal'

# To print top overall results (eg top 10 ranked players), set to True
print_top_ovr_results = True

# To print a summary of an individual player's ranking and best results, set to True.
print_player_info = True

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
winners_df = df[['Winner', 'Event', 'Edition', 'Stage', 'Date']].rename(columns={'Winner': 'Player'})
winners_df['Outcome'] = 'Win'
losers_df = df[['Loser', 'Event', 'Edition', 'Stage', 'Date']].rename(columns={'Loser': 'Player'})
losers_df['Outcome'] = 'Lose'
df = pd.concat([winners_df, losers_df])



# Enter initial point values for each match at notable events
df['Points'] = 0
df['Points'] = df.apply(elo_points, axis=1)




# Make an event results dataframe
# Columns: Player, Event, Edition, Type, Event Points, Event Result (eg. 'Top 8')

event_results_df = df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: points_agg(points, df.loc[points.index, 'Event']))
)
# Add an Event Result column. 
event_results_df['Event_Result'] = event_results_df.apply(get_result, axis=1)


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

# Print top overall results
if print_top_ovr_results:
    print(players_df.head(num_top_players))

# Capitalize player name
player = player.upper()

# Print summary of player's info and best results. 
if not print_player_info:
    pass
elif player in event_results_df['Player'].values:
    best_results = event_results_df.loc[event_results_df['Player'] == player]
    best_results = best_results[['Event', 'Edition', 'Event_Points', 'Event_Result']].sort_values(by='Event_Points', ascending=False)
    best_results = best_results.drop(best_results.loc[best_results['Event_Points'] == 0].index).reset_index(drop=True)
    best_results.index += 1

    wins = players_df.loc[players_df['Player'] == player, 'Wins'].values[0]
    losses = players_df.loc[players_df['Player'] == player, 'Losses'].values[0]

    print(player, ': Ranked number ', players_df.loc[players_df['Player'] == player].index.to_list()[0], ' overall. ', sep='')
    print('Win-loss record: ', wins, '-', losses, '\nTop results:', sep='')
    print(best_results.head(15))
else: 
    print('Player name not found in database. \nMake sure name is spelled correctly.')



# Uncomment for sql style queries
# execute = lambda q: sqldf(q, globals())
# query = "SELECT DISTINCT(Event) FROM df ORDER BY Event"
# query_df = execute(query)
# print(query_df)

