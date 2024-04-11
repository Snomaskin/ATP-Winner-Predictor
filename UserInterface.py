import sys
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QApplication, QLineEdit, \
    QMessageBox
from PredictionModel import ModelOperations

'''
A simple GUI for the user to make prediction request from PredictionModel.
I might implement a feature to interact with the scraper here as well and the circle will be complete.
'''


class MainWindow(QMainWindow):
    def __init__(self, wrapper):
        super().__init__()
        self.wrapper = wrapper
        self.setWindowTitle('Winner Predictor')
        main_window = QWidget()
        self.setCentralWidget(main_window)
        layout = QVBoxLayout()
        main_window.setLayout(layout)

        # Player 1
        self.player1_label = QLabel('Player 1:')
        layout.addWidget(self.player1_label)
        self.player1_input = QLineEdit()
        layout.addWidget(self.player1_input)

        # Player 2
        self.player2_label = QLabel('Player 2:')
        layout.addWidget(self.player2_label)
        self.player2_input = QLineEdit()
        layout.addWidget(self.player2_input)

        # Court surface
        self.courtsurface_label = QLabel('Court Surface:')
        layout.addWidget(self.courtsurface_label)
        self.courtsurface_input = QLineEdit()
        layout.addWidget(self.courtsurface_input)
        self.input_format_label = QLabel("""Input Format:
        Players: 'LastName. FirstNameInitial' (e.g. 'Nadal R.')
        Court Surface Options: 'Hard Court', 'Grass', 'Clay'
        Input is case sensitive""")
        layout.addWidget(self.input_format_label)

        self.button = QPushButton('Predict Winner')
        self.button.clicked.connect(self.on_button_clicked)
        layout.addWidget(self.button)

        # Label to handle prediction output.
        self.result_label = QLabel('')
        layout.addWidget(self.result_label)

    def on_button_clicked(self):
        player1_input = self.player1_input.text()
        player2_input = self.player2_input.text()
        court_surface = self.courtsurface_input.text()

        predicted_winner = self.wrapper.user_input(player1_input, player2_input, court_surface)

        message = f"Predicted winner: {predicted_winner} "
        self.result_label.setText(message)


class Wrapper:
    def __init__(self, model_operations):
        self.model_operations = model_operations

    def user_input(self, player1_name_input: str, player2_name_input: str, court_surface: str) -> [int, float]:
        player1_index, player2_index, court_surface_index = self.index_lookup(player1_name_input, player2_name_input,
                                                                              court_surface)
        predicted_winner_name = self.prediction_output(player1_index, player2_index, court_surface_index)

        return predicted_winner_name

    def index_lookup(self, player1_name: str, player2_name: str, court_surface: str) -> [int, int, int]:
        player1_index, player2_index = self.model_operations.player_index_lookup(player1_name, player2_name)
        court_surface_index = self.model_operations.court_surface_index_lookup(court_surface)

        return player1_index, player2_index, court_surface_index

    def prediction_output(self, player1_index: int, player2_index: int, court_surface_index: int) -> [str, float]:
        prediction_target = self.model_operations.predict_winner(player1_index, player2_index,
                                                                 court_surface_index)
        winner_name = self.model_operations.winner_name(player1_index, player2_index, prediction_target)

        return winner_name


def __main__():
    model_operations = ModelOperations()
    wrapper = Wrapper(model_operations)
    app = QApplication(sys.argv)
    test = MainWindow(wrapper)
    test.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    __main__()
