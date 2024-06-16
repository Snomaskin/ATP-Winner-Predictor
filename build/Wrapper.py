import pandas as pd

from PredictionModel import ModelOperations
from PredictionModel import PrepareDataframe


class PrepareDataframeTest (PrepareDataframe):
    def __init__(self):
        super().__init__()

    def prepare_dataframe(self):
        self.df = self.create_binary_target()
        self.df = self.create_player_index(self.df)
        self.df = self.winner_hash(self.df)
        self.df = self.create_headtohead(self.df)
        player_index_df = pd.read_csv('player_index_df.csv')
        self.df = self.merge_total_wins(self.df, player_index_df)
        self.df = self.encode_df_court_surface(self.df)
        self.export_dataframe(self.df)


class InputHandler:
    def __init__(self):
        self.model_operations = ModelOperations()

    def user_input(self, player1_name: str, player2_name: str, court_surface: str) -> str:
        player1_index, player2_index, court_surface_index = self.index_lookup(player1_name, player2_name,
                                                                              court_surface)
        predicted_winner_name = self.prediction_output(player1_index, player2_index, court_surface_index)

        return predicted_winner_name

    def index_lookup(self, player1_name: str, player2_name: str, court_surface: str) -> [int, int, int]:
        player1_index, player2_index = self.model_operations.player_index_lookup(player1_name, player2_name)
        court_surface_index = self.model_operations.court_surface_index_lookup(court_surface)

        return player1_index, player2_index, court_surface_index

    def prediction_output(self, player1_index: int, player2_index: int, court_surface_index: int) -> str:
        prediction_target = self.model_operations.predict_winner(player1_index, player2_index,
                                                                 court_surface_index)
        winner_name = self.model_operations.winner_name(player1_index, player2_index, prediction_target)

        return winner_name