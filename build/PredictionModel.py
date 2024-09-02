import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import hashlib
# from sklearn.preprocessing import LabelEncoder
# from sklearn.metrics import accuracy_score
import numpy as np
import os


'''
PrepareDataframe:
Takes a dataset (format below) and converts it's contents into a format prediction models can handle.
Input: data.db
Output: model_dataframe.csv, player_index.csv, court_surface_index.csv

 CREATE TABLE "MensATPSingles" (
            EventID TEXT,
            MatchID TEXT PRIMARY KEY,
            MatchDate TEXT, 
            Player1 TEXT,
            Player1Country TEXT,
            Player2 TEXT, 
            Player2Country TEXT,
            Winner TEXT,
            Loser TEXT)

ModelOperations:
Various functions to interact with the dataset. Can be mapped to an API (see API.py).

Known issues:
Prediction output 'winner_name' remains consistent when players have met each other before (headtohead score >0 or <0) but
can return different values if names are switched for 'Player1' and 'Player2' when they have not. I believe it has to do
with how the prediction model evaluates feature importance. Total wins should be higher than it is (around 10%) but I
don't know how to make it so.
'''


class PrepareDataframe:
    def __init__(self):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT * FROM MensATPSingles')
        results = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        self.df = pd.DataFrame(results, columns=columns)
        self.conn.close()

    def create_binary_target(self):
        # Drop column not needed for the prediction algorithm.
        columns_drop = ['EventID', 'Player1Country', 'Player2Country', 'MatchDate', 'EventName']
        sub_df = self.df.drop(columns=columns_drop)

        sub_df['Target'] = 0
        # Iterate over each row in the DataFrame & assign target 1/0 based on which player won.
        # 1 = Player1 win
        # 0 = Player2 win
        for index, row in self.df.iterrows():
            if row['Winner'] == row['Player1']:
                sub_df.at[index, 'Target'] = 1
            elif row['Winner'] == row['Player2']:
                sub_df.at[index, 'Target'] = 0
        sub_df.drop(columns=['Winner', 'Loser'], inplace=True)

        return sub_df

    def calc_headtohead(self, df):
        # Variable to measure total wins/losses in matchup between Player1 and Player2.
        df['HeadToHead'] = 0
        for index, row in df.iterrows():
            # Calculate instances of 'Player1' vs 'Player2' where 'Target' = 1.
            player1_wins = (df[(df['Player1'] == row['Player1']) & (df['Player2'] == row['Player2'])][
                                'Target'] == 1).sum()
            # Same as above but in reverse. (I know it's a bit confusing that df['Player1'] is row[PLayer2]).
            # I have another way of doing this further down which might be easier to follow.
            df.at[index, 'HeadToHead'] = player1_wins - ((df[(df['Player1'] == row['Player2']) & (
                    df['Player2'] == row['Player1'])]['Target'] == 1).sum())  # Calculate win-loss difference

        return df

    def make_player_index(self, df, filename='player_index_df.csv'):
        # Concatenate Player1 and Player2 into one list (contains duplicates).
        players = pd.concat([df['Player1'], df['Player2']], ignore_index=True)

        # Remove duplicates.
        unique_names = players.unique()

        # Create a dictionary mapping unique names to unique IDs starting from 1
        name_to_number = {name: i + 1 for i, name in enumerate(unique_names)}
        df['Player1'] = df['Player1'].map(name_to_number)
        df['Player2'] = df['Player2'].map(name_to_number)

        # Create a player index used for lookup starting from 1.
        player_index_df = pd.DataFrame({'Player': unique_names, 'Index': range(1, len(unique_names) + 1)})

        # Calculate total wins for each player to store in the player index.
        player_index_df = self.calculate_total_wins(df, player_index_df)
        player_index_df.to_csv(filename, index=False)
        print(f"Player index exported to {filename}")

        return df

    def calculate_total_wins(self, df, player_index_df):
        player_index_df['TotalWins'] = 0

        for index, row in player_index_df.iterrows():
            player_index = row['Index']
            wins_as_player1 = df.loc[(df['Player1'] == player_index) & (df['Target'] == 1), 'Target'].count()
            player_index_df.loc[index, 'TotalWins'] += wins_as_player1

        for index, row in player_index_df.iterrows():
            player_index = row['Index']
            wins_as_player2 = df.loc[(df['Player2'] == player_index) & (df['Target'] == 0), 'Target'].count()
            player_index_df.loc[index, 'TotalWins'] += wins_as_player2

        return player_index_df

    def make_court_surface_index(self, filename='court_surface_index_df.csv'):
        court_surface_index_df = pd.DataFrame({'CourtSurface': ['Hard Court', 'Clay', 'Grass'], 'Index': [1, 2, 3]})
        court_surface_index_df.to_csv(filename, index=False)
        print(f"Dataframe exported to {filename}")

    def encode_df_court_surface(self, df):
        # Replace CourtSurface entries from dataset with their indexed values from above.
        # OBS this function also removes all entries where CurtSurface is missing.
        index = pd.read_csv('court_surface_index_df.csv')
        encoded_df = pd.merge(df, index, how='left', on='CourtSurface')
        encoded_df.drop(columns=['CourtSurface'], inplace=True)
        encoded_df.rename(columns={'Index': 'CourtSurface'}, inplace=True)
        encoded_df.dropna(subset=['CourtSurface'], inplace=True)

        return encoded_df

    def matchup_hash(self, df):
        # Hash Player1(index) and Player2(index). Winner first.
        # Reason for this is to even out the bias towards either Player1 or Player2 in the dataset->
        # where a player appears more in either column.
        df['WinnerLoserHash'] = 0
        for index, row in df.iterrows():
            hasher = hashlib.sha256()
            player1 = str(row['Player1'])
            player2 = str(row['Player2'])
            target = row['Target']
            if target == 1:
                player1_winner = [player1, player2]
                combined_players = "#".join(player1_winner)
                hasher.update(combined_players.encode('utf-8'))
                hash = hasher.hexdigest()
                # Hasher returns a hex value that's too long for the prediction model to handle, so it must be shortened.
                short_hash = hash[:12]
                # The prediction model also can't handle hex values, so it has to be converted to an integer.
                normalized_hash = int(short_hash, 16)
                df.at[index, 'WinnerLoserHash'] = normalized_hash

            elif target == 0:
                player2_winner = [player2, player1]
                combined_players = "#".join(player2_winner)
                hasher.update(combined_players.encode('utf-8'))
                hash = hasher.hexdigest()
                short_hash = hash[:12]
                normalized_hash = int(short_hash, 16)
                df.at[index, 'WinnerLoserHash'] = normalized_hash

        return df

    def merge_total_wins(self, df, player_index_df):
        merged_df = pd.merge(df, player_index_df, left_on='Player1', right_on='Index', how='left')
        merged_df.rename(columns={'TotalWins': 'TotalWins_Player1'}, inplace=True)

        merged_df = pd.merge(merged_df, player_index_df, left_on='Player2', right_on='Index', how='left',
                             suffixes=('_Player1', '_Player2'))
        merged_df.rename(columns={'TotalWins': 'TotalWins_Player2'}, inplace=True)
        merged_df.drop(columns=['Player_Player1', 'Index_Player1', 'Player_Player2', 'Index_Player2'], inplace=True)

        return merged_df

    def export_dataframe(self, df, filename='model_df.csv'):
        df.to_csv(filename, index=False)
        print(f"Dataframe exported to {filename}")

    def prepare_dataframe(self):
        self.df = self.create_binary_target()
        self.df = self.create_player_index(self.df)
        self.df = self.winner_hash(self.df)
        self.df = self.create_headtohead(self.df)
        player_index_df = pd.read_csv('player_index_df.csv')
        self.df = self.merge_total_wins(self.df, player_index_df)
        self.df = self.encode_df_court_surface(self.df)
        self.export_dataframe(self.df)

class ModelOperations:
    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        model_df_path = os.path.join(script_dir, 'tables', 'model_df.csv')
        player_index_df_path = os.path.join(script_dir, 'tables', 'player_index_df.csv')
        court_surface_index_df_path = os.path.join(script_dir, 'tables', 'court_surface_index_df.csv')

        self.model_df = pd.read_csv(model_df_path)
        self.player_index_df = pd.read_csv(player_index_df_path)
        self.court_surface_index_df = pd.read_csv(court_surface_index_df_path)

    def preprocessing(self, df):
        x = df.drop(columns=['Target', 'MatchID', 'WinnerLoserHash'])
        y = df['Target']

        return x, y

    def model_evaluation(self):
        x, y = self.preprocessing(self.model_df)
        # I have just used standard values for these:
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

        model_1 = RandomForestClassifier(random_state=42, n_estimators=500, n_jobs=-1, verbose=0,
                                         class_weight='balanced')
        model_1.fit(x_train, y_train)

        # feature_importances = model_1.feature_importances_

        # Visualize feature importances
        # plt.figure(figsize=(10, 6))
        # plt.bar(range(len(feature_importances)), feature_importances, tick_label=x_train.columns)
        # plt.xlabel('Features')
        # plt.ylabel('Feature Importance')
        # plt.title('Feature Importance')
        # plt.xticks(rotation=45)
        # plt.show()

        # Test accuracy of model for dataset
        # pred = model_1.predict(x_test)
        # print(accuracy_score(y_test, pred))

        return model_1

    def player_index_lookup(self, player_name: str) -> int:
        # Lookup player names with their indices in 'player_index.csv'.
        player_index = self.player_index_df[self.player_index_df['Player'] == player_name]['Index'].values
        if len(player_index) == 0:
            raise ValueError(f"No match found for '{player_name}'. Please check spelling and input format.")
        else:

            return player_index[0]
        
    def player_name_lookup(self, player_index: int) -> str:
        player_name = self.player_index_df[self.player_index_df['Index'] == player_index]['Player'].values

        return player_name[0]

    def court_surface_index_lookup(self, surface_name: str) -> int:
        # Lookup court surface with its index value in 'court_surface_index.csv'.
        surface_index_lookup = \
            self.court_surface_index_df[self.court_surface_index_df['CourtSurface'] == surface_name]['Index'].values
        if len(surface_index_lookup) == 0:
            raise ValueError(f"No match found for '{surface_name}'. Please check spelling and input format.")
        else:

            return surface_index_lookup[0]
        
    def court_surface_name_lookup(self, surface_index: int) -> str:
        surface_name_lookup = self.court_surface_index_df[self.court_surface_index_df['Index'] == surface_index]['CourtSurface'].values

        return surface_name_lookup[0]

    def calculate_headtohead(self, player1_index: int, player2_index: int) -> int:
        # Grab all rows where player1_index vs player2_index and vice versa.
        player1_vs_player2 = self.model_df[
            ((self.model_df['Player1'] == player1_index) & (self.model_df['Player2'] == player2_index)) |
            ((self.model_df['Player1'] == player2_index) & (self.model_df['Player2'] == player1_index))
            ]
        # Count the number of rows where each player has Target == 1 means Player1 wins.
        # Returns a tuple (num_rows, num_columns). .shape[0] accesses the first element of the tuple.
        player1_wins_target1 = (player1_vs_player2[(player1_vs_player2['Player1'] == player1_index) &
                                                   (player1_vs_player2['Target'] == 1)]).shape[0]
        player2_wins_target1 = (player1_vs_player2[(player1_vs_player2['Player1'] == player2_index) &
                                                   (player1_vs_player2['Target'] == 1)]).shape[0]
        headtohead_value = player1_wins_target1 - player2_wins_target1

        return headtohead_value

    def predict_winner(self, player1_index: int, player2_index: int, court_surface_index: int) -> [int, float]:
        headtohead_value = self.calculate_headtohead(player1_index, player2_index)
        # players_hash = self.hash_players_input(player1_index, player2_index)
        # Input data must follow the order in which they appear in the dataframe or else specify with 'columns='.
        input_data = pd.DataFrame({
            'Player1': [player1_index],
            'Player2': [player2_index],
            # 'WinnerLoserHash': [np.nan],
            'HeadToHead': [headtohead_value],
            'TotalWins_Player1': [None],
            'TotalWins_Player2': [None],
            'CourtSurface': [court_surface_index]
        })  # columns=['Player1', 'Player2', 'WinnerLoserHash', 'HeadToHead', 'CourtSurface'])

        model = self.model_evaluation()
        prediction_target = model.predict(input_data)

        return prediction_target

    def winner_name(self, player1_index: int, player2_index: int, prediction: int) -> str:
        predicted_winner_index = player1_index if prediction == 1 else player2_index
        predicted_winner_name = \
            self.player_index_df[self.player_index_df['Index'] == predicted_winner_index]['Player'].values[0]

        return predicted_winner_name

    def total_wins_lookup(self, player_index: int) -> int:
        player1_match = self.model_df[self.model_df['Player1'] == player_index]
        if not player1_match.empty:
            return int(player1_match.iloc[0]['TotalWins_Player1'])
        
        player2_match = self.model_df[self.model_df['Player2'] == player_index]
        if not player2_match.empty:
            return int(player2_match.iloc[0]['TotalWins_Player2'])
    
    def nemesis_lookup(self, player_index:int) -> str:
        player1_matches = self.model_df[self.model_df['Player1'] == player_index]
        player2_matches = self.model_df[self.model_df['Player2'] == player_index]

        player1_head_to_head = player1_matches[['Player2', 'HeadToHead']]
        player2_head_to_head = player2_matches[['Player1', 'HeadToHead']]
        player2_head_to_head.loc[:, 'HeadToHead'] = player2_head_to_head['HeadToHead'].abs()

        player1_head_to_head.columns = ['Opponent', 'HeadToHead']
        player2_head_to_head.columns = ['Opponent', 'HeadToHead']

        combined_head_to_head = pd.concat([player1_head_to_head, player2_head_to_head])

        nemesis_row = combined_head_to_head.loc[combined_head_to_head['HeadToHead'].idxmax()]
        nemesis_player_index = nemesis_row['Opponent']
        nemesis_player = self.player_name_lookup(nemesis_player_index)

        return str(nemesis_player)
    
    def favorite_surface(self, player_index:int) -> str:
        player1_wins = self.model_df[(self.model_df['Player1'] == player_index) & (self.model_df['Target'] == 1)]
        player2_wins = self.model_df[(self.model_df['Player2'] == player_index) & (self.model_df['Target'] == 0)]

        combined_wins = pd.concat([player1_wins, player2_wins])
        surface_index = combined_wins['CourtSurface'].mode().iloc[0]
        surface_name = self.court_surface_name_lookup(surface_index)

        return str(surface_name)