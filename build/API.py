from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from PredictionModel import ModelOperations
from contextlib import asynccontextmanager


class PredictionRequest(BaseModel):
    player1: str
    player2: str
    court_surface: str


class PlayerStatsLookup(BaseModel):
    player: str


class InputHandler(ModelOperations):
    def __init__(self):
        super().__init__()

    def prediction_request(self, player1_name: str, player2_name: str, court_surface: str) -> str:
        player1_index = self.player_index_lookup(player1_name)
        player2_index = self.player_index_lookup(player2_name)
        court_surface_index = self.court_surface_index_lookup(court_surface)
        prediction_target = self.predict_winner(player1_index, player2_index, court_surface_index)
        predicted_winner_name = self.winner_name(player1_index, player2_index, prediction_target)

        return f"Predicted Winner: {predicted_winner_name}"

    def player_stats_lookup_request(self, player_name:str) -> str:
        player_index = self.player_index_lookup(player_name)
        total_wins = self.total_wins_lookup(player_index)
        nemesis = self.nemesis_lookup(player_index)
        favorite_surface = self.favorite_surface(player_index)

        return f"""Total Wins: {total_wins}

                    Nemesis: {nemesis}

                    Favorite Surface: {favorite_surface}"""
    

@asynccontextmanager
async def lifespan(app: FastAPI):
        handler = InputHandler()
        app.state.handler = handler
        yield

app = FastAPI(lifespan=lifespan)

origins = [    
    "https://storage.googleapis.com",
    "https://storage.cloud.google.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict_winner")
async def winner_prediction(request_data: PredictionRequest):
    try:
        predicted_winner_name = app.state.handler.prediction_request(request_data.player1, request_data.player2, request_data.court_surface)
        return PlainTextResponse(predicted_winner_name)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/lookup_player_stats")
async def player_stats_lookup(request_data: PlayerStatsLookup):
    try:
        player_stats = app.state.handler.player_stats_lookup_request(request_data.player)
        return PlainTextResponse(player_stats)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    #port = int(os.environ.get("PORT", 8000))
    uvicorn.run("API:app", host="0.0.0.0", port=8080)