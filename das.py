import pandas as pd
from datetime import datetime, timedelta
from pandasql import sqldf
from helpers import get_stage, get_edition, split_edition, modify_event, das_points, ctdas_points, points_agg, ctdas_points_agg, top_performances # type: ignore

pd.set_option('display.max_rows', None)

# Filter data for only the prior n years
num_years = 5

# Count the top n performances in the given timeframe
num_performances = 10

# Print top n players
num_top_players = 20

# Decide whether to drop friendlies or include them
drop_friendlies = True
    


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

# Split Info column into an edition column and a stage column. Original Info column was not consistent. 
ct_das_df['Stage'] = ct_das_df.apply(get_stage, axis=1)
ct_das_df['Edition'] = ct_das_df.apply(get_edition, axis=1)

# For events with the edition in the event name, move the edition to the edition column
ct_das_df['Edition'] = ct_das_df.apply(split_edition, axis=1).fillna('NA')
ct_das_df['Event'] = ct_das_df.apply(modify_event, axis=1).fillna('NA')

ct_das_df = ct_das_df[['Player', 'Event', 'Edition', 'Stage', 'Date', 'Outcome', 'Points']]

print(ct_das_df.loc[ct_das_df['Event'] == 'CT DAS'])


# print(ct_das_df.loc[ct_das_df['Event'] == 'CT DAS'])

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


# Make an event results dataframe
# Columns: Player, Event, Edition, Type, Result

event_results_df = df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: points_agg(points, df.loc[points.index, 'Event']))
)

ctdas_results_df = ct_das_df.groupby(['Player', 'Event', 'Edition'], as_index=False).agg(
    Event_Points = ('Points', lambda points: ctdas_points_agg(points, ct_das_df.loc[points.index, 'Edition']))
)

ctdas_results_df = ctdas_results_df.sort_values(by='Event_Points')
# print(ctdas_results_df.tail(100))

# Add Total Points column to dataframe
player_points = event_results_df.groupby('Player')['Event_Points'].agg(top_performances, num_performances)
players_df['Total_Points'] = players_df['Player'].map(player_points)
players_df['Total_Points'] = players_df['Total_Points'].fillna(0)
players_df['Total_Points'] = players_df['Total_Points'].astype(int)
players_df = players_df.sort_values(by='Total_Points', ascending=False).reset_index(drop=True)
players_df.index += 1

# print(players_df.head(20))

player = "ROBIN"
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

# print(ct_das_df.loc[(ct_das_df['Event'] == 'CT DAS Minor'), ['Edition', 'Stage']])

# print(df.loc[(df['Event'] == 'CTM Lone Star DAS'), ['Edition', 'Stage']])


# execute = lambda q: sqldf(q, globals())
# query = "SELECT * FROM df WHERE Event LIKE '%CT DAS%' ORDER BY Date"
# query_df = execute(query)
# print(query_df)

# print(df.info())
