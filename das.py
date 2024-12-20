import pandas as pd
from datetime import datetime, timedelta
from pandasql import sqldf
from helpers import get_stage, get_edition, get_result, split_edition, modify_event, das_points, ctdas_points, points_agg, ctdas_points_agg, top_performances # type: ignore

pd.set_option('display.max_rows', None)

# Filter data for only the prior n years
num_years = 1

# Count the top n performances in the given timeframe
num_performances = 3

# Print top n players
num_top_players = 10

# Decide whether to drop friendlies or include them
drop_friendlies = True

# Modify player name to access summary of other players.
player = 'pixelandy'

# To print top overall results (eg top 10 ranked players), set to True
print_top_ovr_results = True

# To print a summary of an individual player's ranking and best results, set to True.
print_player_info = True




# Google sheets CSV export URL format
sheet_id = "1nEN0MAbueG36UDkpfUsPZEmAMuKif6IcLAmJ8iZhCe8"
gid = "805197322"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Read specified columns into a dataframe
cols = range(1,9)
df = pd.read_csv(url, usecols=cols)

dasplayers = pd.concat([df['Player1'], df['Player2']]).unique()
dasplayers = sorted(dasplayers)
print('Number of players in dasplayers:', len(dasplayers))
# Drop blank column and rename columns
df = df.drop(['Unnamed: 5'], axis=1)
df = df.rename(columns={'Player1': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Player2': 'Loser', 'Edition/Round': 'Info', 'Date/Time (UTC)': 'Date'})


# Fill null event entries
df['Event'] = df['Event'].fillna("NA")

# Normalize spellings
df['Event'] = df['Event'].str.replace('Das', 'DAS')
for x in ['-final', '-Final', '-finals', '-Finals']:
    df['Info'] = df['Info'].str.replace(x, 'finals')
df['Info'] = df['Info'].str.replace('Final', 'Finals')
df['Info'] = df['Info'].str.replace('Finalss', 'Finals')

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

# Handle CT DAS separately because of weird tournament format: play 3 (or 5) sets, each set is first to 2 (or 3).. whoever wins 2 (or 3) sets wins the match.
ct_das_df = df[df['Event'].str.contains('CT DAS')]

# Split Info column into an edition column and a stage column. Original Info column was not consistent. 
df['Stage'] = df.apply(get_stage, axis=1)
df['Edition'] = df.apply(get_edition, axis=1)

# For events with the edition in the event name, move the edition to the edition column
df['Edition'] = df.apply(split_edition, axis=1).fillna('NA')
df['Event'] = df.apply(modify_event, axis=1).fillna('NA')

df = df[['Winner', 'Wins', 'Losses', 'Loser', 'Event', 'Edition', 'Stage', 'Date']]



# Make sure CT DAS sets have a consistent choice of player1 by sorting alphabetically. Note that "winner" will temporarily be an inaccurate name for the column.
switch = ct_das_df['Winner'] > ct_das_df['Loser']
ct_das_df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = ct_das_df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values

# Only keep last set of each set of sets. 
ct_das_df = ct_das_df.drop_duplicates(['Winner', 'Loser', 'Event', 'Info'], keep='last')


# Move the winners back to column 1
switch = ct_das_df['Wins'] < ct_das_df['Losses']
ct_das_df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = ct_das_df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values


ct_das_winners = ct_das_df[['Winner', 'Event', 'Info', 'Date']].rename(columns={'Winner': 'Player'})
ct_das_winners['Outcome'] = 'Win'
ct_das_losers = ct_das_df[['Loser', 'Event', 'Info', 'Date']].rename(columns={'Loser': 'Player'})
ct_das_losers['Outcome'] = 'Lose'
ct_das_df = pd.concat([ct_das_winners, ct_das_losers])

ct_das_df['Points'] = 0
ct_das_df['Points'] = ct_das_df.apply(ctdas_points, axis=1)

ct_das_df = ct_das_df.reset_index(drop=True)

# Give Andy extra points since his opponent was DQ'd and his win wasn't recorded
ct_das_df.loc[278, 'Points'] = 3

# Split Info column into an edition column and a stage column. Original Info column was not consistent. 
ct_das_df['Stage'] = ct_das_df.apply(get_stage, axis=1)
ct_das_df['Edition'] = ct_das_df.apply(get_edition, axis=1)

# For events with the edition in the event name, move the edition to the edition column
ct_das_df['Edition'] = ct_das_df.apply(split_edition, axis=1).fillna('NA')
ct_das_df['Event'] = ct_das_df.apply(modify_event, axis=1).fillna('NA')

ct_das_df = ct_das_df[['Player', 'Event', 'Edition', 'Stage', 'Date', 'Outcome', 'Points']]


# Drop duplicate rows
df = df.drop_duplicates(['Winner', 'Wins', 'Losses', 'Loser', 'Event', 'Edition', 'Stage', 'Date'])



# Reshape dataframe
winners_df = df[['Winner', 'Event', 'Edition', 'Stage', 'Date']].rename(columns={'Winner': 'Player'})
winners_df['Outcome'] = 'Win'
losers_df = df[['Loser', 'Event', 'Edition', 'Stage', 'Date']].rename(columns={'Loser': 'Player'})
losers_df['Outcome'] = 'Lose'
df = pd.concat([winners_df, losers_df])

# Enter initial point values for each match at notable events
df['Points'] = 0
df['Points'] = df.apply(das_points, axis=1)

# Create players dataframe
# Columns: Player, Wins, Losses, Total_Points (to come later)
players_df = df.groupby(['Player', 'Outcome']).size().unstack(fill_value=0)
players_df = players_df.rename(columns={'Win': 'Wins', 'Lose': 'Losses'})
players_df = players_df.rename_axis(None, axis=1).reset_index()
players_df = players_df[['Player', 'Wins', 'Losses']]

# Now that we've counted ALL wins and losses, we can drop CT DAS events. (Then add them back in later)
df = df.drop(df[df['Event'].str.contains('CT DAS')].index)


# Make event results dataframes
# Columns: Player, Event, Edition, Type, Result

event_results_df = df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: points_agg(points, df.loc[points.index, 'Event']))
)

ctdas_results_df = ct_das_df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: ctdas_points_agg(points, ct_das_df.loc[points.index, 'Edition']))
)

# Combine event results
event_results_df = pd.concat([event_results_df, ctdas_results_df], axis=0)
event_results_df = event_results_df.sort_values(by='Event_Points')

# Add an Event Result column. 
event_results_df['Event_Result'] = event_results_df.apply(get_result, axis=1)

# Add Total Points column to dataframe
player_points = event_results_df.groupby('Player')['Event_Points'].agg(top_performances, num_performances)
players_df['Total_Points'] = players_df['Player'].map(player_points)
players_df['Total_Points'] = players_df['Total_Points'].fillna(0)
players_df['Total_Points'] = players_df['Total_Points'].astype(int)
players_df = players_df.sort_values(by='Total_Points', ascending=False).reset_index(drop=True)
players_df.index += 1

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






# execute = lambda q: sqldf(q, globals())
# query = "SELECT * FROM df WHERE Event LIKE '%CT DAS%' ORDER BY Date"
# query_df = execute(query)
# print(query_df)

# print(df.info())
