from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from Wrapper import InputHandler
from pydantic import BaseModel
from uvicorn import run


app = FastAPI()
handler = InputHandler()

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

class PlayerStatsLookup(Basemodel):
    player: str


@app.post("/winner_predict")
async def prediction_request(request_data: PredictionRequest):
    try:
        winner_name = handler.prediction_request(request_data.player1, request_data.player2, request_data.court_surface)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return winner_name

@app.post("/player_stats")
async def stats_lookup(player_name: PlayerStatsLookup):
    try:
        player_stats = handler.player_stats_lookup_request(player_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return player_stats


if __name__ == "__main__":
    run("API:app",host="0.0.0.0", port=8000)

