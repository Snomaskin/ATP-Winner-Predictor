import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import hashlib
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import numpy as np
import matplotlib.pyplot as plt


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
Predicts the winner between two players using the RandomForest prediction model.
Input(user): player1_name, player2_name, court_surface
Output: winner_name

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
        # Drop column not needed for prediction algorithm.
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

    def create_headtohead(self, df):
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

    def create_player_index(self, df):
        # Concatenate Player1 and Player2 into one list (contains duplicates).
        players = pd.concat([df['Player1'], df['Player2']], ignore_index=True)

        # Create an array of players where name is unique.
        unique_names = players.unique()

        # Create a dictionary mapping unique names to unique IDs starting from 1
        name_to_number = {name: i + 1 for i, name in enumerate(unique_names)}
        df['Player1'] = df['Player1'].map(name_to_number)
        df['Player2'] = df['Player2'].map(name_to_number)

        # Create a player index used for lookup starting from 1.
        player_index_df = pd.DataFrame({'Player': unique_names, 'Index': range(1, len(unique_names) + 1)})

        # Calculate total wins for each player to store in the player index.
        player_index_df = self.calculate_total_wins(df, player_index_df)
        player_index_df.to_csv('player_index_df.csv', index=False)
        print("Player index exported to player_index.csv")

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

    def create_court_surface_index(self):
        court_surface_index = pd.DataFrame({'CourtSurface': ['Hard Court', 'Clay', 'Grass'], 'Index': [1, 2, 3]})
        court_surface_index.to_csv(court_surface_index.csv, index=False)
        print(f"Dataframe exported to court_surface_index.csv")

    def encode_df_court_surface(self, df, index_filename: str):
        # Replace CourtSurface entries from dataset with their indexed values from above.
        # OBS this function also removes all entries where CurtSurface is missing.
        index = pd.read_csv(index_filename)
        encoded_df = pd.merge(df, index, how='left', on='CourtSurface')
        encoded_df.drop(columns=['CourtSurface'], inplace=True)
        encoded_df.rename(columns={'Index': 'CourtSurface'}, inplace=True)

        return encoded_df

    def winner_hash(self, df):
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
                # Hasher returns a hex value that's too long for the prediction model to handle, so we need to shorten it.
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

        merged_df = pd.merge(merged_df, player_index_df, left_on='Player2', right_on='Index', how='left', suffixes=('_Player1', '_Player2'))
        merged_df.rename(columns={'TotalWins': 'TotalWins_Player2'}, inplace=True)
        merged_df.drop(columns=['Player_Player1', 'Index_Player1', 'Player_Player2', 'Index_Player2'], inplace=True)

        return merged_df

    def export_dataframe(self, df, filename='model_dataframe.csv'):
        df.to_csv(filename, index=False)
        print(f"Dataframe exported to {filename}")


class ModelOperations:
    def __init__(self):
        self.model_df = pd.read_csv('model_dataframe.csv')
        self.player_index_df = pd.read_csv('player_index.csv')
        self.court_surface_index = pd.read_csv('court_surface_index.csv')

    def preprocessing(self, df):
        x = df.drop(columns=['Target', 'MatchID', 'WinnerLoserHash'])
        y = df['Target']

        return x, y

    def model_evaluation(self):
        x, y = self.preprocessing(self.model_df)
        # I have just used standard values for these:
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

        model_1 = RandomForestClassifier(random_state=42, n_estimators=500, n_jobs=-1, verbose=0, class_weight='balanced')
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
        pred = model_1.predict(x_test)
        print(accuracy_score(y_test, pred))

        return model_1

    def player_index_lookup(self, player1_name: str, player2_name: str) -> [int, int]:
        # Lookup player names with their indices in 'player_index.csv'.
        player1_index_lookup = self.player_index_df[self.player_index_df['Player'] == player1_name]['Index'].values
        player2_index_lookup = self.player_index_df[self.player_index_df['Player'] == player2_name]['Index'].values
        if len(player1_index_lookup) == 0 or len(player2_index_lookup) == 0:
            print("One or more player missing or is misspelled")

            return None, None
        else:

            return player1_index_lookup[0], player2_index_lookup[0]

    def court_surface_index_lookup(self, court_surface: str) -> int or None:
        # Lookup court surface with its index value in 'court_surface_index.csv'.
        court_surface_index_lookup = \
            self.court_surface_index[self.court_surface_index['CourtSurface'] == court_surface]['Index'].values
        if len(court_surface_index_lookup) == 0:
            print(f"""{court_surface} is either misspelled or does not exist in the database.
                  Possible values: Hard Court, Clay, Grass""")

            return None
        else:

            return court_surface_index_lookup[0]

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
            #'WinnerLoserHash': [np.nan],
            'HeadToHead': [headtohead_value],
            'TotalWins_Player1': [np.nan],
            'TotalWins_Player2': [np.nan],
            'CourtSurface': [court_surface_index]
        }) # columns=['Player1', 'Player2', 'WinnerLoserHash', 'HeadToHead', 'CourtSurface'])

        model = self.model_evaluation()
        prediction_target = model.predict(input_data)

        return prediction_target

    def winner_name(self, player1_index: int, player2_index: int, prediction: int) -> str:
        predicted_winner_index = player1_index if prediction == 1 else player2_index
        predicted_winner_name = \
            self.player_index_df[self.player_index_df['Index'] == predicted_winner_index]['Player'].values[0]

        return predicted_winner_name

    # def hash_players_input(self, player1_index: int, player2_index: int) -> int:
        # This is not needed since we can feed the model missing values (I did not know this before I made this method).
        # hasher = hashlib.sha256()
        # player1 = str(player1_index)
        # player2 = str(player2_index)
        # players = [player1, player2]
        # Sort to fight bias when players are switched.
        # players.sort()
        # combined_players = "#".join(players)
        # hasher.update(combined_players.encode('utf-8'))
        # hash = hasher.hexdigest()
        # short_hash = hash[:12]
        # normalized_hash = int(short_hash, 16)

        #return normalized_hash