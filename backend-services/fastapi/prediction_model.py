import os
import pandas as pd
# import numpy as np
# from sklearn.preprocessing import LabelEncoder
# from sklearn.metrics import accuracy_score
# from google.cloud import storage
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


class ModelOperations:
    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        model_df_path = os.path.join(script_dir, 'tables', 'model_df.csv')
        player_index_df_path = os.path.join(script_dir, 'tables', 'player_index_df.csv')
        court_surface_index_df_path = os.path.join(script_dir, 'tables', 'court_surface_index_df.csv')

        self.model_df = pd.read_csv(model_df_path)
        self.player_index_df = pd.read_csv(player_index_df_path)
        self.court_surface_index_df = pd.read_csv(court_surface_index_df_path)
        #self.model_df = self.read_read_csv_from_gcs("atp-winner-predict", "tables/model_df.csv")
        #self.player_index_df = self.read_read_csv_from_gcs("atp-winner-predict", "tables/player_index_df.csv")
        #self.court_surface_index_df = self.read_read_csv_from_gcs("atp-winner-predict", "tables/court_surface_index_df.csv")

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
        player_name_normalized = player_name.strip().lower()
        normalized_players = self.player_index_df['Player'].str.strip().str.lower()
        
        player_index = self.player_index_df[normalized_players == player_name_normalized]['Index'].values
        if len(player_index) == 0:
            raise ValueError(f"No match found for '{player_name}'. Please check spelling and input format.")
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

    def predict_winner(self, player1_index: int, player2_index: int, court_surface_index: int) -> int:
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
    
    def read_csv_from_gcs(bucket_name, file_name):
        gcs_path = f"gs://{bucket_name}/{file_name}"
        df = pd.read_csv(gcs_path)

        return df
    

class ApiRequestHandler(ModelOperations):
    def __init__(self):
        super().__init__()
        
    def winner_prediction(self, player1_name: str, player2_name: str, court_surface: str) -> str:
        player1_index = self.player_index_lookup(player1_name)
        player2_index = self.player_index_lookup(player2_name)
        court_surface_index = self.court_surface_index_lookup(court_surface)
        prediction_target = self.predict_winner(player1_index, player2_index, court_surface_index)
        predicted_winner_name = self.winner_name(player1_index, player2_index, prediction_target)

        return f"Predicted Winner: {predicted_winner_name}"
    
    def stats_lookup(self, player_name:str) -> str:
        player_index = self.player_index_lookup(player_name)
        total_wins = self.total_wins_lookup(player_index)
        nemesis = self.nemesis_lookup(player_index)
        favorite_surface = self.favorite_surface(player_index)

        return f"""Total Wins: {total_wins}

                    Nemesis: {nemesis}

                    Favorite Surface: {favorite_surface}"""