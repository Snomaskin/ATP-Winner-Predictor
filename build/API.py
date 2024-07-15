from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uvicorn import run
from PredictionModel import ModelOperations


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://tennis-winner-predictor.s3-website.eu-north-1.amazonaws.com", 
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    player1: str
    player2: str
    court_surface: str


class PlayerStatsLookup(BaseModel):
    player: str


@app.post("/predict_winner")
async def prediction_request(request_data: PredictionRequest):
    try:
        predicted_winner_name = handler.prediction_request(request_data.player1, request_data.player2, request_data.court_surface)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return predicted_winner_name


@app.post("/lookup_player_stats")
async def stats_lookup(player_name: PlayerStatsLookup):
    try:
        player_stats = int(handler.player_stats_lookup_request(player_name.player))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return player_stats


class InputHandler(ModelOperations):
    def __init__(self):
        super().__init__()

    def prediction_request(self, player1_name: str, player2_name: str, court_surface: str) -> str:
        player1_index = self.player_index_lookup(player1_name)
        player2_index = self.player_index_lookup(player2_name)
        court_surface_index = self.court_surface_index_lookup(court_surface)
        prediction_target = self.predict_winner(player1_index, player2_index, court_surface_index)
        predicted_winner_name = self.winner_name(player1_index, player2_index, prediction_target)

        return predicted_winner_name

    def player_stats_lookup_request(self, player_name: str) -> int:
        player_index = self.player_index_lookup(player_name)
        total_wins = self.lookup_total_wins(player_index)

        return total_wins


if __name__ == "__main__":
    run("API:app", host="0.0.0.0", port=8000)

handler = InputHandler()
