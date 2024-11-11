from flask import Flask, render_template, request # type: ignore
import pandas as pd
from datetime import datetime, timedelta
from helpers import elo_points, das_points, ctdas_points, points_agg, ctdas_points_agg, get_result, top_performances, modify_event, get_stage, get_edition, split_edition

app = Flask(__name__)


# players_df = players_df.head(num_top_players)
# data = players_df.to_dict(orient='records')

# Info for main matches database
sheet_id = "1Rw1XT90YD8HvYN4JS0Ba1tgkp7UlrG4ksPuP4Yc4SNM"
gid = "658545272"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Read the data from main matches database into a DataFrame
cols = range(0,12)
ovr_df = pd.read_csv(url, usecols=cols)
ovr_df = ovr_df.rename(columns={'Result': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Unnamed: 4': 'Loser', 'Date/time': 'Date', 'Round/game': 'Stage', 'Restreamer/location': 'Location'})
ovr_df.drop(['Unnamed: 5'], axis = 1, inplace = True) 

# Convert dates to datetime
ovr_df['Date'] = pd.to_datetime(ovr_df['Date'], format='%d/%m/%Y %H:%M:%S')

# Some rows have wins < losses. Normalize rows so that the winner is always on the left.
switch = ovr_df['Wins'] < ovr_df['Losses']
ovr_df.loc[switch, ['Winner', 'Loser', 'Wins', 'Losses']] = ovr_df.loc[switch, ['Loser', 'Winner', 'Losses', 'Wins']].values 

# Reshape dataframe 
winners_df = ovr_df[['Winner', 'Event', 'Edition', 'Stage', 'Date', 'Type']].rename(columns={'Winner': 'Player'})
winners_df['Outcome'] = 'Win'
losers_df = ovr_df[['Loser', 'Event', 'Edition', 'Stage', 'Date', 'Type']].rename(columns={'Loser': 'Player'})
losers_df['Outcome'] = 'Lose'
ovr_df = pd.concat([winners_df, losers_df])

# Only keep ELO matches 
ovr_df = ovr_df[ovr_df['Type'] == 'ELO']





# Get list of players from main dataframe
# eloplayers = pd.concat([ovr_df['Winner'], ovr_df['Loser']]).unique()
eloplayers = ovr_df['Player'].unique()
eloplayers = sorted(eloplayers)


# Info for DAS matches database
sheet_id = "1nEN0MAbueG36UDkpfUsPZEmAMuKif6IcLAmJ8iZhCe8"
gid = "805197322"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# Read specified columns into a dataframe
cols = range(1,9)
das_df = pd.read_csv(url, usecols=cols)
dasplayers = pd.concat([das_df['Player1'], das_df['Player2']]).unique()
dasplayers = sorted(dasplayers)


# Drop blank column and rename columns
das_df = das_df.drop(['Unnamed: 5'], axis=1)
das_df = das_df.rename(columns={'Player1': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Player2': 'Loser', 'Edition/Round': 'Info', 'Date/Time (UTC)': 'Date'})


# Fill null event entries
das_df['Event'] = das_df['Event'].fillna("NA")

# Normalize spellings
das_df['Event'] = das_df['Event'].str.replace('Das', 'DAS')
for x in ['-final', '-Final', '-finals', '-Finals']:
    das_df['Info'] = das_df['Info'].str.replace(x, 'finals')
das_df['Info'] = das_df['Info'].str.replace('Final', 'Finals')
das_df['Info'] = das_df['Info'].str.replace('Finalss', 'Finals')

# # Drop friendly events
# if drop_friendlies:
drop_list = ['Friendlies', 'Friendlies: Retribution', 'Friendlies: Rivals', 'LATAM Friendlies', 'LYMYMI Tournament', 'Tetris Friendlies', 'TNP']
das_df = das_df[~das_df['Event'].isin(drop_list)]


# Move the winners to column 1
switch = das_df['Wins'] < das_df['Losses']
das_df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = das_df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values

# Convert dates to datetime format
das_df['Date'] = pd.to_datetime(das_df['Date'], format='%d/%m/%Y %H:%M:%S')

# Replace null values for Event column
das_df['Event'] = das_df['Event'].fillna('None')




@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route('/rankings', methods=['GET', 'POST'])
def rankings():
    # Filter data for only the prior n years
    num_years = int(request.form.get('num_years', 2))

    # Count the top n performances in the given timeframe
    num_performances = int(request.form.get('num_top_performances', 10))

    # Print top n players
    num_top_players = int(request.form.get('num_players', 15))

    # Make a deep copy of the dataframe
    df = ovr_df.copy(deep=True)

    # Filter rows with dates within the last n years
    time_frame = datetime.now() - timedelta(days= num_years * 365 + 1)
    df = df[df['Date'] >= time_frame]

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

    # Only display top number of players
    players_df = players_df.head(num_top_players)

    # Convert to dictionary to read into html file
    data = players_df.reset_index().to_dict(orient='records')

    


    return render_template('rankings.html', data=data, num_years=num_years, num_performances=num_performances, num_top_players=num_top_players)


@app.route("/dasrankings", methods=['GET', 'POST'])
def dasrankings():
    # Filter data for only the prior n years
    num_years = int(request.form.get('num_years', 2))

    # Count the top n performances in the given timeframe
    num_performances = int(request.form.get('num_top_performances', 6))

    # Print top n players
    num_top_players = int(request.form.get('num_players', 15))

    # # Decide whether to drop friendlies or include them
    # drop_friendlies = True






    df = das_df.copy(deep=True)

    # # Drop blank column and rename columns
    # df = df.drop(['Unnamed: 5'], axis=1)
    # df = df.rename(columns={'Player1': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Player2': 'Loser', 'Edition/Round': 'Info', 'Date/Time (UTC)': 'Date'})


    # # Fill null event entries
    # df['Event'] = df['Event'].fillna("NA")

    # # Normalize spellings
    # df['Event'] = df['Event'].str.replace('Das', 'DAS')
    # for x in ['-final', '-Final', '-finals', '-Finals']:
    #     df['Info'] = df['Info'].str.replace(x, 'finals')
    # df['Info'] = df['Info'].str.replace('Final', 'Finals')
    # df['Info'] = df['Info'].str.replace('Finalss', 'Finals')

    # # Drop friendly events
    # if drop_friendlies:
    #     drop_list = ['Friendlies', 'Friendlies: Retribution', 'Friendlies: Rivals', 'LATAM Friendlies', 'LYMYMI Tournament', 'Tetris Friendlies', 'TNP']
    #     df = df[~df['Event'].isin(drop_list)]


    # # Move the winners to column 1
    # switch = df['Wins'] < df['Losses']
    # df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values

    # # Convert dates to datetime format
    # df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S')

    # # Replace null values for Event column
    # df['Event'] = df['Event'].fillna('None')

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

    # Only display top number of players
    players_df = players_df.head(num_top_players)
    
    # Convert to dictionary to read into html file
    data = players_df.reset_index().to_dict(orient='records')

    return render_template('dasrankings.html', data=data, num_years=num_years, num_performances=num_performances, num_top_players=num_top_players)


@app.route("/playerinfo", methods=['GET', 'POST'])
def playerinfo():
    """Display player summaries"""
    num_years = int(request.form.get('num_years', 2))

    # Count the top n performances in the given timeframe
    num_performances = int(request.form.get('num_top_performances', 10))

    player = request.form.get('player', 'FRACTAL')
    player = player.upper()
    
    # Make copy of dataframe
    df = ovr_df.copy(deep=True)

    # Filter rows with dates within the last n years
    time_frame = datetime.now() - timedelta(days= num_years * 365 + 1)
    df = df[df['Date'] >= time_frame]

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

    best_results = event_results_df.loc[event_results_df['Player'] == player]
    best_results = best_results[['Event', 'Edition', 'Event_Points', 'Event_Result']].sort_values(by='Event_Points', ascending=False)
    best_results = best_results.drop(best_results.loc[best_results['Event_Points'] == 0].index).reset_index(drop=True)
    best_results.index += 1
    best_results = best_results.head(num_performances)
    # Convert to dictionary to read into html file
    data = best_results.to_dict(orient='records')

    # Get player ranking
    if players_df['Player'].eq(player).any():
        ranking = players_df.loc[players_df['Player'] == player].index.to_list()[0]

        # Get win-loss record
        win_list = players_df.loc[players_df['Player'] == player, 'Wins']
        loss_list = players_df.loc[players_df['Player'] == player, 'Losses']

        wins = win_list.iloc[0] if not win_list.empty else 0
        losses = loss_list.iloc[0] if not loss_list.empty else 0

    else: 
        ranking = len(dasplayers)
        wins = 0
        losses = 0

    return render_template("playerinfo.html", data=data, player=player, ranking=ranking, wins=wins, losses=losses, eloplayers=eloplayers, num_years=num_years, num_performances=num_performances)


@app.route("/dasplayerinfo", methods=['GET', 'POST'])
def dasplayerinfo():
    """Display player summary for DAS players"""
    num_years = int(request.form.get('num_years', 2))

    # Count the top n performances in the given timeframe
    num_performances = int(request.form.get('num_top_performances', 6))

    player = request.form.get('player', 'Pixelandy')
    player = player.upper()

    # Decide whether to drop friendlies or include them
    # drop_friendlies = True

    # Google sheets CSV export URL format
    # sheet_id = "1nEN0MAbueG36UDkpfUsPZEmAMuKif6IcLAmJ8iZhCe8"
    # gid = "805197322"

    # url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    # # Read specified columns into a dataframe
    # cols = range(1,9)
    # df = pd.read_csv(url, usecols=cols)

    # Drop blank column and rename columns
    df = das_df.copy(deep=True)

    # df = df.drop(['Unnamed: 5'], axis=1)
    # df = df.rename(columns={'Player1': 'Winner', 'Unnamed: 2': 'Wins', 'Unnamed: 3': 'Losses', 'Player2': 'Loser', 'Edition/Round': 'Info', 'Date/Time (UTC)': 'Date'})


    # # Fill null event entries
    # df['Event'] = df['Event'].fillna("NA")

    # # Normalize spellings
    # df['Event'] = df['Event'].str.replace('Das', 'DAS')
    # for x in ['-final', '-Final', '-finals', '-Finals']:
    #     df['Info'] = df['Info'].str.replace(x, 'finals')
    # df['Info'] = df['Info'].str.replace('Final', 'Finals')
    # df['Info'] = df['Info'].str.replace('Finalss', 'Finals')

    # # Drop friendly events
    # if drop_friendlies:
    #     drop_list = ['Friendlies', 'Friendlies: Retribution', 'Friendlies: Rivals', 'LATAM Friendlies', 'LYMYMI Tournament', 'Tetris Friendlies', 'TNP']
    #     df = df[~df['Event'].isin(drop_list)]


    # Move the winners to column 1
    # switch = df['Wins'] < df['Losses']
    # df.loc[switch, ['Winner', 'Wins', 'Losses', 'Loser']] = df.loc[switch, ['Loser', 'Losses', 'Wins', 'Winner']].values

    # # Convert dates to datetime format
    # df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S')

    # # Replace null values for Event column
    # df['Event'] = df['Event'].fillna('None')

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
    
    # Keep selected columns only
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

    best_results = event_results_df.loc[event_results_df['Player'] == player]
    best_results = best_results[['Event', 'Edition', 'Event_Points', 'Event_Result']].sort_values(by='Event_Points', ascending=False)
    best_results = best_results.drop(best_results.loc[best_results['Event_Points'] == 0].index).reset_index(drop=True)
    best_results.index += 1
    best_results = best_results.head(num_performances)
    # Convert to dictionary to read into html file
    data = best_results.to_dict(orient='records')

    # Get player ranking
    if players_df['Player'].eq(player).any():
        ranking = players_df.loc[players_df['Player'] == player].index.to_list()[0]

        # Get win-loss record
        win_list = players_df.loc[players_df['Player'] == player, 'Wins']
        loss_list = players_df.loc[players_df['Player'] == player, 'Losses']

        wins = win_list.iloc[0] if not win_list.empty else 0
        losses = loss_list.iloc[0] if not loss_list.empty else 0

    else: 
        ranking = len(dasplayers)
        wins = 0
        losses = 0



    # Redirect user to login form
    return render_template("dasplayerinfo.html", data=data, player=player, ranking=ranking, wins=wins, losses=losses, dasplayers=dasplayers, num_years=num_years, num_performances=num_performances)


if __name__ == '__main__':
    app.run(debug=False)
